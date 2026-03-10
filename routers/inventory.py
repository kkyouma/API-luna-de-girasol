"""Inventory management endpoints."""

import logging
from datetime import UTC, datetime

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import (
    InventoryItem,
    InventoryItemCreate,
    InventoryItemRead,
    InventoryItemUpdate,
    ProductCatalog,
)
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/low-stock", response_model=list[InventoryItemRead])
def get_low_stock_items(
    session: Session = Depends(get_session),
) -> list[InventoryItem]:
    """Get inventory items below reorder level."""
    statement = select(InventoryItem).where(
        InventoryItem.current_stock <= InventoryItem.reorder_level,
    )
    return list(session.exec(statement).all())


@router.get("/", response_model=list[InventoryItemRead])
def get_inventory(session: Session = Depends(get_session)) -> list[InventoryItem]:
    """Get all inventory items."""
    statement = select(InventoryItem).order_by(InventoryItem.variant_name)
    return list(session.exec(statement).all())


@router.get("/{item_id}", response_model=InventoryItemRead)
def get_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Get a specific inventory item."""
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


@router.post("/", response_model=InventoryItemRead)
def create_inventory_item(
    item: InventoryItemCreate,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Add a new inventory item."""
    product = session.get(ProductCatalog, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db_item = InventoryItem.model_validate(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    logger.info("Added inventory item for product %d", item.product_id)
    return db_item


@router.put("/{item_id}", response_model=InventoryItemRead)
def update_inventory_item(
    item_id: int,
    item_update: InventoryItemUpdate,
    session: Session = Depends(get_session),
) -> InventoryItem:
    """Update an inventory item."""
    db_item = session.get(InventoryItem, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    item_data = item_update.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)

    db_item.updated_at = datetime.now(tz=UTC)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_inventory_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete an inventory item."""
    item = session.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    session.delete(item)
    session.commit()
    return {"message": f"Inventory item {item_id} deleted successfully"}
