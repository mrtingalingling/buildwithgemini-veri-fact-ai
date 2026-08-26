import asyncio
from typing import Any

from google.cloud import firestore

# Use the explicitly provided project ID to avoid deployment issues with project numbers
PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"
COLLECTION_NAME = "fact_checks"

# Initialize Firestore client
db = firestore.AsyncClient(project=PROJECT_ID)

async def save_fact_check(claim: str, hallucination_likelihood: float, verdict: str, sources: list[str]) -> dict[str, Any]:
    """Saves a verified fact-check to the Firestore catalog.

    Args:
        claim: The original claim that was fact-checked.
        hallucination_likelihood: The calculated likelihood (0-100) that the claim is a hallucination/false.
        verdict: A short summary of the verdict (e.g., "True", "False", "Misleading").
        sources: A list of source URLs or names used to verify the claim.

    Returns:
        A dictionary containing the status of the operation and the document ID.
    """
    try:
        doc_ref = db.collection(COLLECTION_NAME).document()
        await doc_ref.set({
            "claim": claim,
            "hallucination_likelihood": hallucination_likelihood,
            "verdict": verdict,
            "sources": sources,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return {"status": "success", "message": f"Fact-check saved with ID {doc_ref.id}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def get_fact_checks(limit: int = 10) -> dict[str, Any]:
    """Retrieves recent fact-checks from the Firestore catalog.

    Args:
        limit: The maximum number of fact-checks to retrieve (default: 10).

    Returns:
        A dictionary containing the status and the retrieved fact-checks.
    """
    try:
        fact_checks_ref = db.collection(COLLECTION_NAME).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        docs = fact_checks_ref.stream()
        
        results = []
        async for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "timestamp" in data and data["timestamp"]:
                data["timestamp"] = data["timestamp"].isoformat()
            results.append(data)
            
        return {"status": "success", "data": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}
