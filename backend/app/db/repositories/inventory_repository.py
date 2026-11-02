
from sqlalchemy.orm import Session

from backend.app.db.models import InventorySnapshot


def get_product_inventory(db: Session, product_id: str):
    return (
        db.query(InventorySnapshot)
        .filter(InventorySnapshot.product_id == product_id)
        .first()
    )


def get_all_inventory(db: Session):
    return db.query(InventorySnapshot).all()


def get_available_stock(db: Session, product_id: str):
    inventory = get_product_inventory(db, product_id)

    if inventory is None:
        return None

    return inventory.available_stock


def get_low_stock_products(db: Session):
    return (
        db.query(InventorySnapshot)
        .filter(
            InventorySnapshot.available_stock
            <= InventorySnapshot.reorder_level
        )
        .all()
   )
