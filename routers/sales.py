"""Sales order endpoints."""

import logging
from datetime import UTC, datetime

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import (
    InventoryItem,
    SaleOrder,
    SaleOrderCreate,
    SaleOrderItem,
    SaleOrderRead,
    SaleOrderReadWithDetails,
    StockMovement,
    StockMovementType,
    StockReferenceType,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/", response_model=list[SaleOrderRead])
def get_sales(session: Session = Depends(get_session)) -> list[SaleOrder]:
    """Get all sale orders, newest first."""
    statement = select(SaleOrder).order_by(SaleOrder.created_at.desc())
    return list(session.exec(statement).all())


@router.get("/{sale_id}", response_model=SaleOrderReadWithDetails)
def get_sale(
    sale_id: int,
    session: Session = Depends(get_session),
) -> SaleOrder:
    """Get a specific sale order with its items."""
    statement = (
        select(SaleOrder)
        .where(SaleOrder.id == sale_id)
        .options(selectinload(SaleOrder.items))
    )
    sale = session.exec(statement).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale order not found")
    return sale


@router.post("/", response_model=SaleOrderReadWithDetails)
def create_sale(
    sale_data: SaleOrderCreate,
    session: Session = Depends(get_session),
) -> SaleOrder:
    """Create a new sale order.

    The server calculates subtotal and total from items automatically.
    Stock is validated for ALL items before any changes are persisted.
    """
    if not sale_data.items:
        raise HTTPException(400, "Sale must have at least one item")

    # 1. Fetch all referenced inventory items in one query
    inventory_ids = [
        item.inventory_item_id for item in sale_data.items if item.inventory_item_id
    ]
    inventory_map: dict[int, InventoryItem] = {}
    if inventory_ids:
        statement = select(InventoryItem).where(InventoryItem.id.in_(inventory_ids))
        inventory_map = {item.id: item for item in session.exec(statement).all()}

    # 2. Validate ALL items BEFORE creating anything
    for item_data in sale_data.items:
        if item_data.inventory_item_id and item_data.bouquet_template_id:
            raise HTTPException(400, "Item cannot reference both inventory and bouquet")
        if not item_data.inventory_item_id and not item_data.bouquet_template_id:
            raise HTTPException(400, "Item must reference inventory or bouquet")

        if item_data.inventory_item_id:
            inv_item = inventory_map.get(item_data.inventory_item_id)
            if not inv_item:
                raise HTTPException(
                    404, f"Inventory item {item_data.inventory_item_id} not found"
                )
            if inv_item.current_stock < item_data.quantity:
                raise HTTPException(
                    400,
                    f"Insufficient stock for '{inv_item.variant_name}'. "
                    f"Required: {item_data.quantity}, "
                    f"Available: {inv_item.current_stock}",
                )

    # 3. Create sale order (server sets order_date)
    db_sale = SaleOrder(
        order_date=datetime.now(tz=UTC),
        order_type=sale_data.order_type.value,
        customer_id=sale_data.customer_id,
        occasion_id=sale_data.occasion_id,
        subtotal=0,
        total=0,
        discount_percent=sale_data.discount_percent,
        discount_amount=sale_data.discount_amount,
        packaging_fee=sale_data.packaging_fee,
        status=sale_data.status.value,
        notes=sale_data.notes,
    )
    session.add(db_sale)
    session.flush()

    # 4. Process items, deduct stock, create movements
    running_subtotal = 0.0
    stock_movements: list[StockMovement] = []

    for item_data in sale_data.items:
        if item_data.inventory_item_id:
            inv_item = inventory_map[item_data.inventory_item_id]
            unit_price = (
                item_data.unit_price
                if item_data.unit_price is not None
                else inv_item.unit_price
            )
        else:
            unit_price = item_data.unit_price or 0

        line_subtotal = item_data.quantity * unit_price

        db_item = SaleOrderItem(
            sale_order_id=db_sale.id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            subtotal=line_subtotal,
            description=item_data.description,
            inventory_item_id=item_data.inventory_item_id,
            bouquet_template_id=item_data.bouquet_template_id,
        )
        session.add(db_item)
        running_subtotal += line_subtotal

        # Deduct stock for inventory items
        if item_data.inventory_item_id:
            inv_item = inventory_map[item_data.inventory_item_id]
            inv_item.current_stock -= item_data.quantity
            session.add(inv_item)

            stock_movements.append(
                StockMovement(
                    movement_type=StockMovementType.OUT.value,
                    quantity=item_data.quantity,
                    reference_type=StockReferenceType.SALE.value,
                    reference_id=db_sale.id,
                    inventory_item_id=inv_item.id,
                    notes=f"Sale #{db_sale.id}",
                )
            )

    session.add_all(stock_movements)

    # 5. Calculate totals server-side
    db_sale.subtotal = running_subtotal
    discount = (
        running_subtotal * sale_data.discount_percent / 100
    ) + sale_data.discount_amount
    db_sale.total = running_subtotal - discount + sale_data.packaging_fee

    session.commit()
    session.refresh(db_sale)

    logger.info("Created sale #%s — total: %s", db_sale.id, db_sale.total)
    return db_sale
