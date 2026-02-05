"""Pytest fixtures for API testing."""

from collections.abc import Generator
from datetime import datetime

import pytest
from api import app
from database import get_session
from fastapi.testclient import TestClient
from models import InventoryItem, ProductCatalog
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture(name="engine")
def fixture_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def fixture_session(engine) -> Generator[Session]:
    """Create a database session for testing."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def fixture_client(session: Session) -> Generator[TestClient]:
    """Create a test client with overridden database dependency."""

    def get_session_override() -> Generator[Session]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="sample_product")
def fixture_sample_product(session: Session) -> ProductCatalog:
    """Create a sample product in the database."""
    product = ProductCatalog(
        name="Red Rose",
        category="Flowers",
        description="Beautiful red rose",
        care_instructions="Keep in water, avoid direct sunlight",
        created_at=datetime.now(),
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@pytest.fixture(name="sample_inventory_item")
def fixture_sample_inventory_item(
    session: Session,
    sample_product: ProductCatalog,
) -> InventoryItem:
    """Create a sample inventory item in the database."""
    item = InventoryItem(
        product_id=sample_product.id,
        variant_name="Large Red Rose",
        sku="ROSE-RED-L",
        unit_cost=500,
        unit_price=1000,
        current_stock=50,
        reorder_level=10,
        shelf_life_days=7,
        is_active=True,
        created_at=datetime.now().replace(microsecond=0),
        updated_at=datetime.now().replace(microsecond=0),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@pytest.fixture(name="low_stock_item")
def fixture_low_stock_item(
    session: Session,
    sample_product: ProductCatalog,
) -> InventoryItem:
    """Create a low-stock inventory item in the database."""
    item = InventoryItem(
        product_id=sample_product.id,
        variant_name="Small Red Rose",
        sku="ROSE-RED-S",
        unit_cost=300,
        unit_price=600,
        current_stock=5,  # Below reorder_level of 10
        reorder_level=10,
        shelf_life_days=7,
        is_active=True,
        created_at=datetime.now().replace(microsecond=0),
        updated_at=datetime.now().replace(microsecond=0),
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item
