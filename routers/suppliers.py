"""Supplier management endpoints."""

import logging

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import Supplier, SupplierCreate, SupplierRead, SupplierUpdate
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/", response_model=list[SupplierRead])
def get_suppliers(session: Session = Depends(get_session)) -> list[Supplier]:
    """Get all suppliers."""
    statement = select(Supplier).order_by(Supplier.name)
    return list(session.exec(statement).all())


@router.get("/{supplier_id}", response_model=SupplierRead)
def get_supplier(
    supplier_id: int,
    session: Session = Depends(get_session),
) -> Supplier:
    """Get a specific supplier."""
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("/", response_model=SupplierRead)
def create_supplier(
    supplier: SupplierCreate,
    session: Session = Depends(get_session),
) -> Supplier:
    """Create a new supplier."""
    db_supplier = Supplier.model_validate(supplier)
    session.add(db_supplier)
    session.commit()
    session.refresh(db_supplier)
    logger.info("Created supplier '%s'", supplier.name)
    return db_supplier


@router.put("/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    supplier_update: SupplierUpdate,
    session: Session = Depends(get_session),
) -> Supplier:
    """Update a supplier."""
    db_supplier = session.get(Supplier, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    update_data = supplier_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_supplier, key, value)

    session.commit()
    session.refresh(db_supplier)
    return db_supplier
