import json
import os

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder


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


# --------------------------------------------------
# Load documents
# --------------------------------------------------

print("Loading RAG documents...")

with open(DOCUMENTS_PATH, "r", encoding="utf-8") as f:
    documents = json.load(f)

print(f"Loaded {len(documents)} documents")


# --------------------------------------------------
# Load FAISS index
# --------------------------------------------------

print("Loading FAISS index...")

faiss_index = faiss.read_index(INDEX_PATH)

print(f"FAISS index contains {faiss_index.ntotal} vectors")


# --------------------------------------------------
# Load BGE-M3
# --------------------------------------------------

print("Loading BGE-M3...")

embedding_model = SentenceTransformer(
    "BAAI/bge-m3"
)

print("BGE-M3 loaded")


# --------------------------------------------------
# Prepare BM25
# --------------------------------------------------

print("Building BM25 index...")

tokenized_documents = [
    document["text"].lower().split()
    for document in documents
]

bm25 = BM25Okapi(tokenized_documents)

print("BM25 index ready")


# --------------------------------------------------
# Load reranker
# --------------------------------------------------

print("Loading BGE reranker...")

reranker = CrossEncoder(
    "BAAI/bge-reranker-base"
)

print("Reranker loaded")


# --------------------------------------------------
# FAISS semantic search
# --------------------------------------------------

def vector_search(query, top_k=10):

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    scores, indices = faiss_index.search(
        query_embedding,
        top_k
    )

    results = []

    for score, index in zip(scores[0], indices[0]):

        if index < 0:
            continue

        results.append({
            "document": documents[index],
            "score": float(score)
        })

    return results


# --------------------------------------------------
# BM25 search
# --------------------------------------------------

def bm25_search(query, top_k=10):

    tokens = query.lower().split()

    scores = bm25.get_scores(tokens)

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in top_indices:

        results.append({
            "document": documents[index],
            "score": float(scores[index])
        })

    return results


# --------------------------------------------------
# Hybrid candidate retrieval
# --------------------------------------------------

def get_candidates(query, top_k=10):

    vector_results = vector_search(
        query,
        top_k
    )

    bm25_results = bm25_search(
        query,
        top_k
    )

    candidates = {}

    # Add semantic results
    for result in vector_results:

        document = result["document"]

        doc_id = document["id"]

        candidates[doc_id] = document

    # Add BM25 results
    for result in bm25_results:

        document = result["document"]

        doc_id = document["id"]

        candidates[doc_id] = document

    return list(candidates.values())


# --------------------------------------------------
# BGE reranking
# --------------------------------------------------

def rerank(query, candidates, top_k=5):

    if not candidates:
        return []

    pairs = [
        (query, document["text"])
        for document in candidates
    ]

    scores = reranker.predict(
        pairs,
        show_progress_bar=False
    )

    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: float(x[1]),
        reverse=True
    )

    results = []

    for document, score in ranked[:top_k]:

        results.append({
            **document,
            "rerank_score": float(score)
        })

    return results