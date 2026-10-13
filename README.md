# RAG-Driven Intelligent Travel Recommendation and Personalized Itinerary Generation System

A local Retrieval-Augmented Generation (RAG) application that recommends travel destinations and generates personalized day-by-day itineraries from a travel knowledge base.

## Overview

Travel planning requires information about destinations, attractions, activities, accommodation, budgets, seasons, and other considerations. This project retrieves relevant travel information and provides it to a local Large Language Model (LLM) to generate contextual recommendations.

The application uses **FastAPI** for the backend and separate **HTML, CSS, and JavaScript** files for the frontend. It is designed without Streamlit, Docker, Qdrant, or paid OpenAI API calls.

## Features

- Natural-language travel queries.
- Personalized destination recommendations and day-by-day itineraries.
- PostgreSQL for structured travel data.
- BGE-M3 embeddings for semantic representation.
- FAISS for local vector indexing and similarity search.
- BM25 keyword retrieval combined with FAISS semantic retrieval.
- BGE Reranker to rank retrieved documents by relevance.
- Ollama for local LLM generation.
- FastAPI backend with a separate HTML/CSS/JavaScript frontend.
- Response-time measurement for retrieval, reranking, generation, and total processing.

## Architecture

```text
User Query
    |
HTML / CSS / JavaScript
    |
FastAPI
    |
RAG Pipeline
    |-- FAISS semantic retrieval
    |-- BM25 keyword retrieval
    |
Hybrid candidates
    |
BGE Reranker
    |
Relevant travel documents
    |
Local Ollama LLM
    |
Personalized recommendation and itinerary
```

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Language | Python | Data processing and application logic |
| Structured database | PostgreSQL | Store structured travel information |
| Embeddings | `BAAI/bge-m3` | Encode travel documents and queries |
| Vector search | FAISS (`IndexFlatIP`) | Local vector indexing and similarity search |
| Keyword retrieval | `rank-bm25` | Lexical matching |
| Reranking | `BAAI/bge-reranker-base` | Rank candidates by relevance |
| Local LLM | Ollama | Generate recommendations using retrieved context |
| Backend | FastAPI | API and frontend serving |
| Frontend | HTML, CSS, JavaScript | User interface |

## Dataset

Input files:

- `india_tourism_dataset.json`
- `dataset_schema.json`
- `google_review_ratings.csv`
- `destination_names.txt`

The processed data includes destinations, attractions, activities, accommodations, budgets, and seasons. The current database load contains 100 destinations, 591 attractions, 363 activities, 306 accommodation records, 300 budget records, and 259 season records.

**Data freshness:** Unless a live data source has been configured, do not treat this application as a source of real-time prices, weather, route conditions, opening hours, or availability.

## RAG Workflow

1. **ETL:** Clean and validate the input data and load structured records into PostgreSQL.
2. **Document creation:** Convert travel information into searchable text documents, stored as `data/processed/rag_documents.json`.
3. **Embedding generation:** Use BGE-M3 to create normalized embeddings.
4. **FAISS indexing:** Build a local vector index and save the index with matching document metadata.
5. **Hybrid retrieval:** Search with FAISS and BM25, then combine candidate results.
6. **Reranking:** Use BGE Reranker to rank candidates against the user query.
7. **Context construction:** Pass the most relevant retrieved documents to the LLM.
8. **Generation:** Use a local Ollama model to generate a response grounded in the retrieved information.
9. **API response:** Return the recommendation and response-time information through FastAPI.

## Project Structure

This is the intended layout; filenames should match your actual working copy.

```text
travel-rag/
├── data/
│   ├── raw/
│   │   ├── india_tourism_dataset.json
│   │   ├── dataset_schema.json
│   │   ├── google_review_ratings.csv
│   │   └── destination_names.txt
│   └── processed/
│       ├── rag_documents.json
│       ├── travel.index
│       └── faiss_documents.json
├── src/
│   ├── __init__.py
│   ├── data/
│   │   ├── etl.py
│   │   ├── create_documents.py
│   │   └── validate_documents.py
│   ├── embeddings/
│   │   └── create_faiss_index.py
│   ├── retrieval/
│   │   └── hybrid_retrieval.py
│   ├── generation/
│   │   └── llm_generator.py
│   ├── rag_pipeline.py
│   ├── api.py
│   └── frontend/
│       ├── index.html
│       ├── css/style.css
│       └── js/app.js
├── .env
├── requirements.txt
└── README.md
```

## Prerequisites

- Python version compatible with the project's dependencies (Python 3.10+ is a reasonable starting point).
- PostgreSQL.
- Ollama.
- The dataset files listed above.

The embedding and reranker models may be downloaded by their model libraries on first use.

## Setup

### 1. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell activation is blocked, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If you do not yet have a complete `requirements.txt`, common packages for this architecture include:

```bash
pip install fastapi "uvicorn[standard]" psycopg2-binary python-dotenv sentence-transformers faiss-cpu rank-bm25 ollama
```

Install any additional packages imported by your actual ETL and API files.

### 3. Configure PostgreSQL

The current development setup uses database `travel_rag` and schema `travel`. Configure your database connection in `.env`. Example:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=travel_rag
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
```

The variable names must match those used by your source code. Do not commit real credentials to version control.

### 4. Start Ollama

Pull the model configured in `src/generation/llm_generator.py`. For example, if your code uses `llama3.2:1b`:

```bash
ollama pull llama3.2:1b
ollama run llama3.2:1b
```

If your code uses a different model name, pull that model instead. The name in code must match the installed model.

### 5. Prepare documents and the FAISS index

Run your ETL script if the database is not already populated, then create the RAG documents and FAISS index.

Example commands, assuming the scripts expose runnable module entry points:

```bash
python -m src.data.create_documents
python -m src.embeddings.create_faiss_index
```

If your scripts are not runnable as modules, use the execution commands documented in those files. Ensure the index and metadata are generated from the same document collection.

### 6. Start FastAPI

From the project root:

```bash
uvicorn src.api:app --reload
```

Open `http://127.0.0.1:8000` in your browser. Adjust the command if your API entry point differs.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Serve the frontend |
| `GET` | `/health` | Check API health |
| `POST` | `/recommend` | Generate a travel recommendation |

Example request body (confirm the field name in `src/api.py`):

```json
{
  "query": "Plan a 3-day trip for two people with a moderate budget. I prefer peaceful nature, waterfalls, sightseeing, and local food."
}
```

The intended response includes the query, generated recommendation, and response time. Confirm the exact schema in your API implementation.

## Example Prompt

Try entering this in the frontend:

> I am planning a 4-day trip to a peaceful hill destination in South India for two people with a moderate budget. I enjoy nature, scenic viewpoints, waterfalls, local food, and relaxed activities. Recommend a suitable destination from your knowledge base and create a day-by-day itinerary. Explain why it matches my preferences and include attractions, activities, accommodation options, the ideal season, and important travel considerations.

## Performance Tips

- Load embedding models, the reranker, and the FAISS index once at application startup.
- Do not re-embed the full document collection for every query.
- Keep the retrieved context relevant and reasonably small.
- Try a lightweight local Ollama model if generation is slow, and evaluate answer quality after changing models.
- Measure retrieval, reranking, LLM generation, and total response times separately.
- Evaluate both speed and retrieval/answer quality.

## Limitations

- Recommendations depend on the completeness and freshness of the available data.
- RAG can reduce unsupported responses but cannot guarantee that every generated statement is correct.
- Real-time weather, route, price, booking, and opening-hour information requires live data integrations.
- Response time and output quality depend on the selected LLM and hardware.
- Users should verify important travel and safety information.

## Future Enhancements

- Integrate reliable live weather and route APIs.
- Improve personalization based on budget, trip duration, interests, and constraints.
- Evaluate retrieval relevance and factual grounding.
- Add caching and optimize reranking and local LLM inference.
- Show sources for retrieved travel facts.

## Author

**Challapalle Venkata Sainath Reddy**  
M.Tech CSE (AI & ML), VIT Chennai  
Registration Number: `25MML1025`

## License and Attribution

Before publishing or redistributing the project, add the appropriate license and attribution details for each dataset and model, and follow their terms of use.
