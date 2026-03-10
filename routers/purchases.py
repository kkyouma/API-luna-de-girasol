"""Purchase order endpoints."""

import logging
from datetime import UTC, datetime

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import (
    InventoryItem,
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderItem,
    PurchaseOrderRead,
    PurchaseOrderReadWithDetails,
    PurchaseOrderStatus,
    StockMovement,
    StockMovementType,
    StockReferenceType,
    Supplier,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.get("/", response_model=list[PurchaseOrderRead])
def get_purchase_orders(
    session: Session = Depends(get_session),
) -> list[PurchaseOrder]:
    """Get all purchase orders, newest first."""
    statement = select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    return list(session.exec(statement).all())


@router.get("/{purchase_id}", response_model=PurchaseOrderReadWithDetails)
def get_purchase_order(
    purchase_id: int,
    session: Session = Depends(get_session),
) -> PurchaseOrder:
    """Get a specific purchase order with supplier and items."""
    statement = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == purchase_id)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.supplier),
        )
    )
    order = session.exec(statement).first()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return order


@router.post("/", response_model=PurchaseOrderReadWithDetails)
def create_purchase_order(
    order_data: PurchaseOrderCreate,
    session: Session = Depends(get_session),
) -> PurchaseOrder:
    """Create a new purchase order.

    The server calculates total_cost and item subtotals automatically.
    """
    supplier = session.get(Supplier, order_data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db_order = PurchaseOrder(
        supplier_id=order_data.supplier_id,
        order_date=datetime.now(tz=UTC),
        delivery_date=order_data.delivery_date,
        total_cost=0,
        status=PurchaseOrderStatus.PENDING,
        notes=order_data.notes,
    )
    session.add(db_order)
    session.flush()

    total_cost = 0.0
    for item_data in order_data.items:
        inv_item = session.get(InventoryItem, item_data.inventory_item_id)
        if not inv_item:
            raise HTTPException(
                404, f"Inventory item {item_data.inventory_item_id} not found"
            )

        line_subtotal = item_data.quantity * item_data.unit_cost
        db_item = PurchaseOrderItem(
            purchase_order_id=db_order.id,
            inventory_item_id=item_data.inventory_item_id,
            quantity=item_data.quantity,
            unit_cost=item_data.unit_cost,
            subtotal=line_subtotal,
        )
        session.add(db_item)
        total_cost += line_subtotal

    db_order.total_cost = total_cost
    session.commit()

    # Reload with relationships for response
    statement = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == db_order.id)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.supplier),
        )
    )
    logger.info("Created purchase order #%s — total: %s", db_order.id, total_cost)
    return session.exec(statement).one()


@router.post("/{purchase_id}/receive", response_model=PurchaseOrderReadWithDetails)
def receive_purchase_order(
    purchase_id: int,
    session: Session = Depends(get_session),
) -> PurchaseOrder:
    """Mark a purchase order as delivered and update inventory stock.

    For each item in the order, increments current_stock and creates
    a StockMovement record of type IN/PURCHASE.

    Raises:
        HTTPException: 404 if order not found, 400 if already delivered/cancelled.
    """
    statement = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == purchase_id)
        .options(selectinload(PurchaseOrder.items))
    )
    order = session.exec(statement).first()
    if not order:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if order.status == PurchaseOrderStatus.DELIVERED:
        raise HTTPException(status_code=400, detail="Order already delivered")
    if order.status == PurchaseOrderStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot receive a cancelled order")

    # Fetch all inventory items in one query
    inv_ids = [item.inventory_item_id for item in order.items]
    inv_items = {
        item.id: item
        for item in session.exec(
            select(InventoryItem).where(InventoryItem.id.in_(inv_ids))
        ).all()
    }

    stock_movements: list[StockMovement] = []
    for item in order.items:
        inv_item = inv_items.get(item.inventory_item_id)
        if not inv_item:
            raise HTTPException(
                404, f"Inventory item {item.inventory_item_id} not found"
            )

        inv_item.current_stock += item.quantity
        session.add(inv_item)

        stock_movements.append(
            StockMovement(
                movement_type=StockMovementType.IN.value,
                quantity=item.quantity,
                reference_type=StockReferenceType.PURCHASE.value,
                reference_id=order.id,
                inventory_item_id=inv_item.id,
                notes=f"Purchase #{order.id}",
            )
        )

    session.add_all(stock_movements)
    order.status = PurchaseOrderStatus.DELIVERED
    order.delivery_date = datetime.now(tz=UTC)

    session.commit()

    # Reload with relationships for response
    statement = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == purchase_id)
        .options(
            selectinload(PurchaseOrder.items),
            selectinload(PurchaseOrder.supplier),
        )
    )
    logger.info("Received purchase order #%s", purchase_id)
    return session.exec(statement).one()
