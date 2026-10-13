import time

from src.retrieval.hybrid_retrieval import (
    get_candidates,
    rerank
)

from src.generation.llm_generator import (
    generate_recommendation
)


def run_rag(query):

    total_start = time.perf_counter()

    # ---------------------------------------------
    # Retrieval
    # ---------------------------------------------

    retrieval_start = time.perf_counter()

    candidates = get_candidates(
        query,
        top_k=10
    )

    retrieval_time = (
        time.perf_counter()
        - retrieval_start
    )

    if not candidates:
        return "No relevant travel destinations were found."


    # ---------------------------------------------
    # Reranking
    # ---------------------------------------------

    rerank_start = time.perf_counter()

    ranked_documents = rerank(
        query,
        candidates,
        top_k=5
    )

    rerank_time = (
        time.perf_counter()
        - rerank_start
    )

    if not ranked_documents:
        return "No relevant travel destinations were found."


    # ---------------------------------------------
    # LLM generation
    # ---------------------------------------------

    llm_start = time.perf_counter()

    answer = generate_recommendation(
        query,
        ranked_documents
    )

    llm_time = (
        time.perf_counter()
        - llm_start
    )


    # ---------------------------------------------
    # Total
    # ---------------------------------------------

    total_time = (
        time.perf_counter()
        - total_start
    )


    print("\n------------------------------")
    print("RAG PERFORMANCE")
    print("------------------------------")
    print(f"Retrieval : {retrieval_time:.2f} sec")
    print(f"Reranking : {rerank_time:.2f} sec")
    print(f"LLM       : {llm_time:.2f} sec")
    print(f"Total     : {total_time:.2f} sec")
    print("------------------------------\n")


    return answer