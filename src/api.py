from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import time

from src.rag_pipeline import run_rag


app = FastAPI(
    title="Travel RAG API",
    description="RAG-based intelligent travel recommendation system",
    version="1.0"
)


# --------------------------------------------------
# Static files
# --------------------------------------------------

app.mount(
    "/css",
    StaticFiles(directory="src/frontend/css"),
    name="css"
)

app.mount(
    "/js",
    StaticFiles(directory="src/frontend/js"),
    name="js"
)


# --------------------------------------------------
# Request model
# --------------------------------------------------

class TravelQuery(BaseModel):
    query: str


# --------------------------------------------------
# Home page
# --------------------------------------------------

@app.get("/")
def home():

    return FileResponse(
        "src/frontend/index.html"
    )


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",
        "system": "Travel RAG"
    }


# --------------------------------------------------
# Recommendation endpoint
# --------------------------------------------------

@app.post("/recommend")
def recommend(request: TravelQuery):

    start_time = time.perf_counter()

    answer = run_rag(
        request.query
    )

    total_time = time.perf_counter() - start_time

    return {
        "query": request.query,
        "recommendation": answer,
        "response_time_seconds": round(
            total_time,
            2
        )
    }