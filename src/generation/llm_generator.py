import ollama


MODEL_NAME = "llama3.2"


def generate_recommendation(query, retrieved_documents):

    context_parts = []

    for i, doc in enumerate(retrieved_documents, start=1):

        context_parts.append(
            f"""
Destination {i}: {doc.get('destination_name', '')}
State: {doc.get('state', '')}
Region: {doc.get('region', '')}

Information:
{doc.get('text', '')}
"""
        )

    context = "\n".join(context_parts)


    prompt = f"""
You are a travel recommendation assistant.

Answer the user's travel request using ONLY the provided travel information.

USER REQUEST:
{query}

RETRIEVED TRAVEL INFORMATION:
{context}

Instructions:

1. Recommend the most relevant destinations.
2. Explain why each destination matches the request.
3. Create a practical day-by-day itinerary.
4. Mention relevant attractions and activities.
5. Mention important travel considerations when available.
6. Do not invent facts that are not present in the retrieved information.
7. If the retrieved information is insufficient, clearly say so.
8. Keep the response concise and useful.
"""


    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.2,
            "num_predict": 700
        }
    )

    return response["message"]["content"]