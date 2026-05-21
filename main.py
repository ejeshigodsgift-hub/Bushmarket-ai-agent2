from fastapi import FastAPI
from api.routes import cooperative_routes

app = FastAPI(title="Bushmarket Cooperative Service")

app.include_router(cooperative_routes.router)