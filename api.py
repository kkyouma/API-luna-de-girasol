"""Luna de Girasol API — FastAPI application setup."""

from fastapi import FastAPI
from routers import catalog, customers, inventory, purchases, sales, suppliers

app = FastAPI(title="Luna de Girasol API")

# =============== ROUTERS ===============

app.include_router(catalog.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(purchases.router)
app.include_router(suppliers.router)
app.include_router(customers.router)


# =============== HEALTH ===============


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "message": "Luna de Girasol API",
        "status": "active",
    }
