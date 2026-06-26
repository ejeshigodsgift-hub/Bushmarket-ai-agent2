class ProductDemandMetric(Base):
    __tablename__ = "product_demand_metrics"

    id
    product_id
    market_id

    search_count
    cart_count
    purchase_count

    demand_score
    updated_at