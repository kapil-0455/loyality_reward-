from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.api.routes.approvals import router as approvals_router
from backend.app.api.routes.customers import router as customers_router
from backend.app.api.routes.recommendations import router as recommendations_router
from backend.app.api.routes.redemptions import router as redemptions_router
from backend.app.observability.logging import RequestIDLoggingMiddleware

load_dotenv()

app = FastAPI(
    title="Loyalty Reward Optimisation API",
    description="Inventory-aware reward recommendation system",
    version="1.0.0",
)

# CORS middleware for cross-origin frontend support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register request-id and structured logging middleware
app.add_middleware(RequestIDLoggingMiddleware)

# Register all routers
app.include_router(customers_router)
app.include_router(recommendations_router)
app.include_router(approvals_router)
app.include_router(redemptions_router)


@app.get("/", include_in_schema=False)
def root():
    """Redirect home route directly to interactive Swagger docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
