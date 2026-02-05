import logging

from models import (
    InventoryItem,
)
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


def get_all_inventory(session: Session) -> list[InventoryItem]:
    """Get all the inventory items."""
    statement = select(InventoryItem).order_by(InventoryItem.variant_name)
    items = list(session.exec(statement).all())
    logger.debug(f"Get {len(items)} items from the inventory")
    return items


# def add_to_catalog(
#     session: Session,
#     name: str,
#     category: str,
#     description: str | None = None,
#     care_instructions: str | None = None,
# ) -> ProductCatalogCreate:
#     """Add a new product to the catalog."""
#     product = ProductCatalog.model_validate(product)
#     session.add(product)
#     session.commit()
#     session.refresh(product)
#     logger.info(f"Added {product.name} to catalog")
#     return product
#
#
# def add_to_inventory(
#     session: Session,
# ): ...
