import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

DOCUMENTS_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "rag_documents.json"
)

INDEX_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "travel.index"
)

METADATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "faiss_documents.json"
)


# --------------------------------------------------
# Load documents
# --------------------------------------------------

print("Loading RAG documents...")

with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
    documents = json.load(f)

print(f"Loaded {len(documents)} documents")


# --------------------------------------------------
# Load BGE-M3
# --------------------------------------------------

print("Loading BGE-M3...")

model = SentenceTransformer("BAAI/bge-m3")

print("BGE-M3 loaded")


# --------------------------------------------------
# Create embeddings
# --------------------------------------------------

texts = [
    document["text"]
    for document in documents
]

print("Creating embeddings...")

embeddings = model.encode(
    texts,
    batch_size=8,
    show_progress_bar=True,
    normalize_embeddings=True
)

embeddings = np.asarray(
    embeddings,
    dtype="float32"
)

print("Embedding shape:", embeddings.shape)


# --------------------------------------------------
# Create FAISS index
# --------------------------------------------------

dimension = embeddings.shape[1]

print(f"Creating FAISS index with dimension {dimension}...")

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print(f"Added {index.ntotal} vectors to FAISS")


# --------------------------------------------------
# Save FAISS index
# --------------------------------------------------

os.makedirs(
    os.path.dirname(INDEX_PATH),
    exist_ok=True
)

faiss.write_index(
    index,
    INDEX_PATH
)

print(f"FAISS index saved to:")
print(INDEX_PATH)


# --------------------------------------------------
# Save document metadata
# --------------------------------------------------

metadata = []

for document in documents:

    metadata.append({
        "id": document.get("id"),
        "destination_name": document.get("destination_name"),
        "state": document.get("state"),
        "region": document.get("region")
    })

with open(
    METADATA_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        metadata,
        f,
        ensure_ascii=False,
        indent=2
    )

print("Document metadata saved to:")
print(METADATA_PATH)

print("\nFAISS index creation completed successfully.")