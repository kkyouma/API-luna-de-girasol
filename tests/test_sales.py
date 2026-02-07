from api import create_sale
from database import get_session
from models import SaleOrderCreate

# Test the endpoint with sample data
test_data = {
    "order_date": "2026-02-06T10:00:00",
    "order_type": "walk-in",
    "discount_percent": 10,
    "discount_amount": 0,
    "packaging_fee": 200,
    "status": "pending",
    "notes": "Valentine's Day pre-order - deliver on Feb 14th",
    "customer_id": 1,
    "occasion_id": 1,
    "items": [{"quantity": 12, "inventory_item_id": 1}],
}


def test_create_sale():
    session = next(get_session())
    try:
        sale_order = SaleOrderCreate(**test_data)
        create_sale(sale_order)

        # Debug the model_dump issue
        print("sale_order:", sale_order)
        print("type:", type(sale_order))

    finally:
        session.close()


if __name__ == "__main__":
    test_create_sale()
