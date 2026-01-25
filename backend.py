"""
Backend module for database
"""

import os
from typing import Literal
import libsql
from dotenv import load_dotenv
import logging
from contextlib import contextmanager
import queries as sql

# =============== CONFIG ===============
# pyright: reportAttributeAccessIssue=false

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# =============== AUTH ===============
load_dotenv()

_url = os.getenv("TURSO_DATABASE_URL")
_token = os.getenv("TURSO_AUTH_TOKEN")

if not _url or not _token:
    raise ValueError("Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN")


# =============== CONECTION MANAGER ===============
@contextmanager
def get_connection():
    conn = None
    try:
        conn = libsql.connect(_url, auth_token=_token)
        yield conn
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error at closing the connection: {e}")


@contextmanager
def transaction(conn: libsql.Connection):
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
        logger.debug("Completed transaction successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction reverted: {e}")
        raise


# =============== QUERY FUNCTIONS ===============


def query(sql: str, params: tuple = ()) -> list[tuple]:
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        logging.debug(f"Query executed successfully: {sql[:50]}")
        cursor.close()
        return rows


def query_one(sql: str, params: tuple = ()):
    with get_connection() as conn:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchone()
        logging.debug(f"Query executed successfully: {sql[:50]}")
        cursor.close()
        return rows


def execute(sql: str, params: tuple = ()) -> int:
    with get_connection() as conn:
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            lastrowid = cursor.lastrowid
            cursor.close()
            return lastrowid
        except Exception as e:
            conn.rollback()
            logger.error(f"Execute failed: {e}")
            raise


# =============== ORDERS ===============


# Orders


def _get_order_details(order_id: int):
    return query_one(sql.GET_ORDER_BY_ID, params=(order_id,))


def _get_pending_orders():
    return query(sql.GET_PENDING_ORDERS)


def _get_order_items(order_id: int):
    return query(sql.GET_ORDER_ITEMS, (order_id,))


# Flowers


def _get_flower_stock(flower_id: int) -> int:
    rows = query(sql.GET_FLOWER_STOCK, (flower_id,))

    return rows[0][0] if rows else 0


def _get_all_flowers():
    return query(sql.GET_ALL_FLOWERS)


def _get_stock_history():
    return query(sql.GET_STOCK_HISTORY)


def _get_all_movements(limit: int = 10):
    return query(sql.GET_STOCK_MOVEMENTS, (limit,))


# Others


def _get_all_occasions():
    return query(sql.GET_ALL_OCCASIONS)


# =============== BUSINESS FUNCTIONS ===============


# NOTE: Verificar query con y sin placeholders
def get_available_stock(
    flower_ids: list[int] | None, conn: libsql.Connection
) -> dict[int, int]:
    """
    Return: {flower_id: available_stock}

    Args:
        flower_ids: Lista de IDs de flores a consultar, o None para consultar todas
        conn: Conexión a la base de datos
    """
    if flower_ids:
        # Si hay IDs específicos, usar WHERE con placeholders
        placeholders = ",".join("?" * len(flower_ids))
        query = sql.GET_AVAILABLE_STOCK + f"\nWHERE f.id IN ({placeholders})"
        results = conn.execute(query, tuple(flower_ids)).fetchall()
    else:
        # Sin IDs, consultar todas las flores
        results = conn.execute(sql.GET_AVAILABLE_STOCK).fetchall()
        logger.debug("Stock obtained")

    return {row[0]: row[1] for row in results}


def create_order_transaction(
    customer_id: int,
    occasion_id: int,
    items: list[dict],
    notes: str = "",
) -> int:
    with get_connection() as conn:
        flowers_ids = [item["flower_id"] for item in items]
        available_stocks = get_available_stock(flowers_ids, conn=conn)

        for item in items:
            available = available_stocks.get(item["flower_id"], 0)

            if available < item["quantity"]:
                flower = conn.execute(
                    sql.GET_FLOWER_BY_ID,
                    item["flower_id"],
                ).fetchone()
                raise ValueError(f"Insuficent stock for '{flower[1]}'")

        with transaction(conn):
            subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
            total = subtotal
            cursor = conn.execute(
                sql.INSERT_ORDER, (customer_id, occasion_id, subtotal, total, notes)
            )
            order_id = cursor.lastrowid

            # NOTE: Si son muchos items (>100) podria ser mejor usar `conn.executemany()`
            for item in items:
                item_subtotal = item["quantity"] * item["unit_price"]

                conn.execute(
                    sql.INSERT_ORDER_ITEM,
                    (
                        order_id,
                        item["flower_id"],
                        item["quantity"],
                        item["unit_price"],
                        item_subtotal,
                    ),
                )

                conn.execute(
                    sql.INSERT_STOCK_MOVEMENT,
                    (
                        item["flower_id"],
                        "out",
                        item["quantity"],
                        order_id,
                        "sale",
                        f"Reservado orden #{order_id}",
                    ),
                )

        return order_id


def fulfill_order_transaction(order_id: int):
    """
    Cambia el estado a 'completed', descuenta stock y genera auditoría.
    """
    with get_connection() as conn:
        with transaction(conn):
            items = conn.execute(
                # NOTE: Aqui solo necesitamos flower_id y quantity; evaluar usar una query mas ligera
                sql.GET_ORDER_ITEMS,
                (order_id,),
            ).fetchall()

        for flower_id, quantity in items:
            conn.execute(sql.UPDATE_STOCK, (quantity, flower_id))
            conn.execute(
                """
                UPDATE stock_movement 
                SET notes = Vendido en ramo # ?
                WHERE flower_id = ?
            """,
                (
                    order_id,
                    flower_id,
                ),
            )

        conn.execute(
            sql.UPDATE_ORDER_STATUS,
            (
                "completed",
                order_id,
            ),
        )

        conn.commit()
        return True


def create_inventory_transaction(
    items: list[dict],
    movement_type: Literal["in", "out"],
    reference_id: int | None = None,
    reference_type: Literal["purchase", "adjustment", "waste"] = "adjustment",
    notes: str | None = None,
):
    """
    items: [{"flower_id": int, "quantity": int}, ...]
    """

    expected_direction = {
        "purchase": "in",
        "waste": "out",
        "adjustment": movement_type,
    }

    if movement_type != expected_direction[reference_type]:
        raise ValueError(
            f"{reference_type} movement must be '{expected_direction[reference_type]}'"
        )

    # Change query according to movement type
    if movement_type == "in":
        update_stock_sql = sql.UPDATE_STOCK_ADD
    elif movement_type == "out":
        update_stock_sql = sql.UPDATE_STOCK_DEDUCT

    with get_connection() as conn:
        with transaction(conn):
            for item in items:
                flower_id = item["flower_id"]
                quantity = item["quantity"]
                # Insertar movimiento
                conn.execute(
                    sql.INSERT_STOCK_MOVEMENT,
                    (
                        flower_id,
                        movement_type,
                        quantity,
                        reference_id,
                        reference_type,
                        notes,
                    ),
                )

                # Actualizar stock
                conn.execute(
                    update_stock_sql,
                    (quantity, flower_id),
                )
