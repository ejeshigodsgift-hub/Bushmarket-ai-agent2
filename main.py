from fastapi import FastAPI

from app.core.config import settings
from app.integrations.kafka_client import event_bus

# =========================
# AUTH ROUTES
# =========================
from app.api.routes.auth import router as auth_router

# =========================
# USER ROUTES
# =========================
from app.api.routes.users import router as users_router

# =========================
# ADMIN ROUTES
# =========================
from app.api.routes.admin import router as admin_router

# =========================
# AGENT ROUTES
# =========================
from app.api.routes.agent import router as agent_router

# =========================
# MARKETPLACE ROUTES
# =========================
from app.api.routes.marketplace import router as marketplace_router

# =========================
# CART ROUTES
# =========================
from app.api.routes.cart import router as cart_router

# =========================
# ORDER ROUTES
# =========================
from app.api.routes.orders import router as orders_router

# =========================
# MIDDLEWARE
# =========================
from app.core.middleware import (
    SessionAuthMiddleware
)


# =====================================================
# FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0"
)


# =====================================================
# MIDDLEWARE REGISTRATION
# =====================================================

app.add_middleware(SessionAuthMiddleware)


# =====================================================
# KAFKA LIFECYCLE
# =====================================================

@app.on_event("startup")
async def startup():

    await event_bus.start()


@app.on_event("shutdown")
async def shutdown():

    await event_bus.stop()


# =====================================================
# ROUTE REGISTRATION
# =====================================================

# AUTH
app.include_router(auth_router)

# USERS
app.include_router(users_router)

# ADMIN
app.include_router(admin_router)

# AGENT
app.include_router(agent_router)

# MARKETPLACE
app.include_router(marketplace_router)

# CART
app.include_router(cart_router)

# ORDERS
app.include_router(orders_router)


# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.ENV
    }


# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():

    return {
        "app": settings.APP_NAME,
        "status": "running",
        "environment": settings.ENV
    }