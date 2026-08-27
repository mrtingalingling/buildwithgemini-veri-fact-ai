import vertexai

CORPUS_NAME = "projects/419816504777/locations/us-central1/ragCorpora/4388872186081837056"
PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"
LOCATION = "us-central1"

def consult_fact_rag_corpus(query: str) -> str:
    """Search the ground-truth fact-check RAG corpus for verified information and guidelines.

    Args:
        query: What to look up (a claim, physics law, historical event, or AI hallucination guideline).
    Returns:
        The matched passages from the corpus, or a note if no relevant information was found.
    """
    from vertexai.preview import rag
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"RAG Corpus Retrieval failed: {e}"
    
    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant passage found in RAG corpus."
