import asyncio
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"
COLLECTION_NAME = "fact_checks"

async def seed():
    print(f"Connecting to Firestore for project {PROJECT_ID}...")
    db = firestore.AsyncClient(project=PROJECT_ID)
    
    seeds = [
        {
            "claim": "The earth is flat.",
            "hallucination_likelihood": 100.0,
            "accuracy_confidence": 0.0,
            "falsehood_confidence": 100.0,
            "verdict": "False",
            "sources": ["https://en.wikipedia.org/wiki/Spherical_Earth"],
            "timestamp": firestore.SERVER_TIMESTAMP
        },
        {
            "claim": "Water boils at 100 degrees Celsius at sea level.",
            "hallucination_likelihood": 0.0,
            "accuracy_confidence": 100.0,
            "falsehood_confidence": 0.0,
            "verdict": "True",
            "sources": ["https://en.wikipedia.org/wiki/Boiling_point"],
            "timestamp": firestore.SERVER_TIMESTAMP
        },
        {
            "claim": "Humans use only 10% of their brains.",
            "hallucination_likelihood": 99.0,
            "accuracy_confidence": 1.0,
            "falsehood_confidence": 99.0,
            "verdict": "False",
            "sources": ["https://en.wikipedia.org/wiki/Ten_percent_of_the_brain_myth"],
            "timestamp": firestore.SERVER_TIMESTAMP
        }
    ]
    
    collection = db.collection(COLLECTION_NAME)
    
    print(f"Seeding {len(seeds)} documents to '{COLLECTION_NAME}' collection...")
    for item in seeds:
        doc_ref = collection.document()
        await doc_ref.set(item)
        print(f"Added document: {doc_ref.id} -> {item['claim']}")
        
    print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
