from fastapi import FastAPI
from app.routers import transactions

app = FastAPI(
    title="Financial Crime Workbench API",
    description="Investigation workbench API for AML transactions, risk, and case management.",
    version="1.0.0",
)

# register routers
app.include_router(transactions.router)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "system": "Financial Crime Workbench API",
        "docs_url": "/docs",
    }
