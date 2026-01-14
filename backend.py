"""
Backend module for database
"""

import os
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


def get_order_details():
    return query_one(sql.GET_ORDER_BY_ID)


def get_pending_orders():
    return query(sql.GET_PENDING_ORDERS)


def get_order_items(order_id: int):
    return query(sql.GET_ORDER_ITEMS, (order_id,))


def get_flower_stock(flower_id: int) -> int:
    sql = """
    SELECT current_stock FROM flower WHERE id = ?
    """
    rows = query(sql, (flower_id,))

    return rows[0][0] if rows else 0


# =============== BUSINESS FUNCTIONS ===============


# NOTE: Verificar query con y sin placeholders
def get_available_stock(
    flower_ids: list[int], conn: libsql.Connection
) -> dict[int, int]:
    """
    Return: {flower_ids, available_stock}
    """
    placeholders = ",".join("?" * len(flower_ids))
    results = conn.execute(
        sql.GET_AVAILABLE_STOCK + f"\nWHERE f.id IN {placeholders}",
        tuple(flower_ids),
    ).fetchall()
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
                flower_name = conn.execute(
                    """
                        SELECT flower_name FROM flower WHERE id = ?
                        """,
                    item["flower_id"],
                ).fetchone()
                raise ValueError(f"Insuficent stock for '{flower_name}'")

        with transaction(conn):
            subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
            total = subtotal

            sql_order = """
            INSERT INTO sale_order (customer_id, occasion_id, order_date, subtotal, total, status, notes)
            VALUES (?, ?, DATE('now'), ?, ?, 'pending', ?)
            """
            cursor = conn.execute(
                sql_order, (customer_id, occasion_id, subtotal, total, notes)
            )
            order_id = cursor.lastrowid

            # NOTE: Si son muchos items (>100) podria ser mejor usar `conn.executemany()`
            for item in items:
                item_subtotal = item["quantity"] * item["unit_price"]

                sql_order_item = """
                INSERT INTO sale_order_item (sale_order_id, flower_id, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?)
                """
                sql_audit = """
                INSERT INTO stock_movement (flower_id, movement_type, quantity, reference_id, reference_type, notes)
                VALUES (?, 'reserved', ?, ?, 'sale_order', ?)
                """

                conn.execute(
                    sql_order_item,
                    (
                        order_id,
                        item["flower_id"],
                        item["quantity"],
                        item["unit_price"],
                        item_subtotal,
                    ),
                )

                conn.execute(
                    sql_audit,
                    (
                        item["flower_id"],
                        item["quantity"],
                        order_id,
                        f"Stock reservado para orden #{order_id}",
                    ),
                )

        return order_id


def fulfill_order_transaction(order_id: int):
    """
    Cambia el estado a 'completed', descuenta stock y genera auditoría.
    """
    with get_connection() as conn:
        # Validate transaction
        with transaction(conn):
            items = conn.execute(
                "SELECT flower_id, quantity FROM sale_order_item WHERE sale_order_id = ?",
                (order_id,),
            ).fetchall()

            sql_update_stock = (
                "UPDATE flower SET current_stock = current_stock - ? WHERE id = ?"
            )
            sql_audit = """
                INSERT INTO stock_movement (flower_id, movement_type, quantity, reference_id, reference_type, notes)
                VALUES (?, 'sale', ?, ?, 'sale_order', ?)
            """

        for flower_id, quantity in items:
            conn.execute(sql_update_stock, (quantity, flower_id))
            conn.execute(
                sql_audit,
                (flower_id, quantity, order_id, f"Orden #{order_id} despachada"),
            )

        conn.execute(
            "UPDATE sale_order SET status = 'completed' WHERE id = ?", (order_id,)
        )

        conn.commit()
        return True
