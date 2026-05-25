from sqlalchemy.orm import Session

from app.db.models.product import Product
from app.db.models.product_variant import ProductVariant


class ProductService:

    # =========================
    # CREATE PRODUCT
    # =========================
    def create_product(
        self,
        db: Session,
        data: dict
    ):

        product = Product(**data)

        db.add(product)
        db.commit()
        db.refresh(product)

        return product

    # =========================
    # GET PRODUCT
    # =========================
    def get_product(
        self,
        db: Session,
        product_id: str
    ):

        return db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()

    # =========================
    # SEARCH PRODUCTS
    # =========================
    def search_products(
        self,
        db: Session,
        keyword: str
    ):

        return db.query(Product).filter(
            Product.name.ilike(f"%{keyword}%"),
            Product.is_active == True
        ).all()


product_service = ProductService()