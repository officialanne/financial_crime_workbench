from fastapi import FastAPI
from app.routers import transactions, risk, dashboard, graph, cases

app = FastAPI(
    title="Financial Crime Workbench API",
    description="Investigation workbench API for AML transactions, risk scoring, network analysis, and case management.",
    version="1.0.0",
)

# register routers
app.include_router(transactions.router)
app.include_router(risk.router)
app.include_router(dashboard.router)
app.include_router(graph.router)
app.include_router(cases.router)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "system": "Financial Crime Workbench API",
        "docs_url": "/docs",
    }
