from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "travel_destinations"

# Load model
model = SentenceTransformer("BAAI/bge-m3")

# Connect Qdrant
client = QdrantClient(
    host=QDRANT_HOST,
    port=QDRANT_PORT
)


def search_destinations(query, top_k=5):

    # Convert query into embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    # Search Qdrant
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding.tolist(),
        limit=top_k
    ).points

    print("\nTop matching destinations:\n")

    for i, result in enumerate(results, 1):

        payload = result.payload

        print(f"{i}. {payload['destination_name']}")
        print(f"   State  : {payload['state']}")
        print(f"   Region : {payload['region']}")
        print(f"   Score  : {result.score:.4f}")
        print()


if __name__ == "__main__":

    query = input("Enter your travel requirement: ")

    search_destinations(query)