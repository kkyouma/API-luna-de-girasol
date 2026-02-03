from sqlmodel import SQLModel


class InventoryItemBase(SQLModel):
    variant_name: str
    current_stock: int
    unit_price: int


class InventoryResponse(InventoryItemBase):
    id: int


class ProductCatalogBase(SQLModel):
    name: str
    category: str
    description: str | None = None
    care_instructions: str | None = None


class ProductCatalogResponse(ProductCatalogBase):
    id: int
