"""Product catalog endpoints."""

import logging

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import (
    ProductCatalog,
    ProductCatalogCreate,
    ProductCatalogRead,
    ProductCatalogReadWithInventory,
)
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/", response_model=list[ProductCatalogRead])
def get_catalog(session: Session = Depends(get_session)) -> list[ProductCatalog]:
    """Get all products from catalog."""
    statement = select(ProductCatalog).order_by(ProductCatalog.name)
    return list(session.exec(statement).all())


@router.get("/{product_id}", response_model=ProductCatalogReadWithInventory)
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> ProductCatalog:
    """Get a specific product with its inventory items."""
    statement = (
        select(ProductCatalog)
        .where(ProductCatalog.id == product_id)
        .options(selectinload(ProductCatalog.inventory_items))
    )
    product = session.exec(statement).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductCatalogRead)
def create_product(
    product: ProductCatalogCreate,
    session: Session = Depends(get_session),
) -> ProductCatalog:
    """Add a new product to the catalog."""
    db_product = ProductCatalog.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    logger.info("Added '%s' to catalog", product.name)
    return db_product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Delete a product from catalog."""
    product = session.get(ProductCatalog, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return {"message": f"Product {product_id} deleted successfully"}
