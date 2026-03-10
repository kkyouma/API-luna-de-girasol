"""Customer management endpoints."""

import logging

from database import get_session
from fastapi import APIRouter, Depends, HTTPException
from models import Customer, CustomerCreate, CustomerRead, CustomerUpdate
from sqlmodel import Session, select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerRead])
def get_customers(session: Session = Depends(get_session)) -> list[Customer]:
    """Get all customers."""
    statement = select(Customer).order_by(Customer.name)
    return list(session.exec(statement).all())


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(
    customer_id: int,
    session: Session = Depends(get_session),
) -> Customer:
    """Get a specific customer."""
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerRead)
def create_customer(
    customer: CustomerCreate,
    session: Session = Depends(get_session),
) -> Customer:
    """Create a new customer."""
    db_customer = Customer.model_validate(customer)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    logger.info("Created customer '%s'", customer.name)
    return db_customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int,
    customer_update: CustomerUpdate,
    session: Session = Depends(get_session),
) -> Customer:
    """Update a customer."""
    db_customer = session.get(Customer, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)

    session.commit()
    session.refresh(db_customer)
    return db_customer
