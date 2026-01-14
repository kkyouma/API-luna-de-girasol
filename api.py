from fastapi import FastAPI
from pydantic import BaseModel

from backend import get_pending_orders

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


# ========== ENDPOINTS ============


@app.get("/")
def root():
    return {"message": "Floristeria API v1.0", "status": "active"}


@app.get("/orders/pending", response_model=list[OrderResponse])
def list_pending_orders():
    rows = get_pending_orders()
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


@app.get("/orders/details")
def get_order_details(order_id: int): ...


# @app.get("/orders", response_model=list[OrderResponse])
# async def create_item(item: OrderItem):
#     return {
#         "item": item,
#         "quantity": item.quantity,
#         "unit_price": item.unit_price,
#         "message": "Item created",
#     }
