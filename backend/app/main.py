
from fastapi import FastAPI

from backend.app.api.routes.approvals import router as approvals_router
from backend.app.api.routes.customers import router as customers_router
from backend.app.api.routes.recommendations import router as recommendations_router
from backend.app.api.routes.redemptions import router as redemptions_router

app = FastAPI(
    title="Loyalty Reward Optimisation API",
    description="Inventory-aware reward recommendation system",
    version="1.0.0"
)

# Register all routers
app.include_router(customers_router)
app.include_router(recommendations_router)
app.include_router(approvals_router)
app.include_router(redemptions_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}
