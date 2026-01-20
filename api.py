from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from backend import (
    _get_pending_orders,
    _get_order_details,
    _get_all_flowers,
    _get_all_occasions,
    _get_order_items,
    create_order_transaction,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Floristeria API Turso")

# ========== MODELS ============


class OrderItem(BaseModel):
    flower_id: int
    quantity: int
    unit_price: float


class OrderResponse(BaseModel):
    id: int
    order_date: int
    total: float
    notes: str
    status: str = "pending"


class CreateOrderRequest(BaseModel):
    customer_id: int
    occasion_id: int
    items: list[OrderItem]
    notes: str = ""


# ========== ENDPOINTS ============


@app.get("/")
def root():
    return {"message": "Floristeria API v1.0", "status": "active"}


@app.get("/orders/pending", response_model=list[OrderResponse])
def get_pending_orders():
    rows = _get_pending_orders()
    return [
        {
            "id": row[0],
            "order_date": row[0],
            "total": row[2],
            "notes": row[3] or "",
            "status": "pending",
        }
        for row in rows
    ]


@app.get("/orders/{order_id}/items")
def get_order_items(order_id: int):
    items = _get_order_items(order_id)
    return [
        {
            "flower_id": item[0],
            "name": item[1],
            "color": item[2],
            "quantity": item[3],
        }
        for item in items
    ]


@app.get("/orders/{order_id}")
def get_order_details(order_id: int):
    order = _get_order_details(order_id)
    items = _get_order_items(order_id)
    return {
        "id": order[0],
        "customer_id": order[1],
        "order_date": order[2],
        "subtotal": order[3],
        "total": order[4],
        "status": order[5],
        "notes": order[6] or "",
        "items": [
            {
                "flower_id": item[0],
                "name": item[1],
                "color": item[2],
                "quantity": item[3],
            }
            for item in items
        ],
    }


@app.get("/flowers/history")
def get_flowers_history(order_id: int):
    items = _get_order_items(order_id)
    return [
        {
            "flower_id": item[0],
            "name": item[1],
            "color": item[2],
            "quantity": item[3],
        }
        for item in items
    ]


@app.post("/orders")
def create_order(order_data: CreateOrderRequest):
    """Crea una nueva orden"""
    try:
        items_dict = [
            {
                "flower_id": item.flower_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order_data.items
        ]

        order_id = create_order_transaction(
            customer_id=order_data.customer_id,
            occasion_id=order_data.occasion_id,
            items=items_dict,
            notes=order_data.notes,
        )

        return {"order_id": order_id, "message": "Orden creada exitosamente"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/flowers")
def get_all_flowers():
    rows = _get_all_flowers()
    return [
        {
            "id": row[0],
            "name": row[1],
            "color": row[2],
            "current_stock": row[3],
            "price": row[4],
        }
        for row in rows
    ]


@app.get("/occasions")
def get_all_occasions():
    rows = _get_all_occasions()
    return [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]


# @app.get("/orders", response_model=list[OrderResponse])
# async def create_item(item: OrderItem):
#     return {
#         "item": item,
#         "quantity": item.quantity,
#         "unit_price": item.unit_price,
#         "message": "Item created",
#     }
