import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"
LOCATION = "us-central1"
GCS_PATH = "gs://ai-fact-checker-assets-qwiklabs-gcp-04-6fd860cf790f/rag/"

PARSING_PROMPT = (
    "Extract the individual useful facts, claims, and guidelines described in this text. "
    "Omit all metadata and boilerplate. Output clean, self-contained prose."
)

def create_and_index():
    print(f"Initializing Vertex AI RAG in {LOCATION} for project {PROJECT_ID}...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 1. Switch region's RAG managed DB to serverless mode
    cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
    try:
        rag.update_rag_engine_config(
            rag_engine_config=rag.RagEngineConfig(
                name=cfg,
                rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
            )
        )
        print("Set serverless mode for RAG Engine.")
    except Exception as e:
        print(f"Config update notice: {e}")

    # 2. Create the corpus
    print("Creating RAG corpus...")
    corpus = rag.create_corpus(
        display_name="fact-checker-corpus",
        embedding_model_config=rag.EmbeddingModelConfig(
            publisher_model="publishers/google/models/text-embedding-005"
        ),
    )
    print(f"Created corpus successfully!")
    print(f"CORPUS_NAME = \"{corpus.name}\"")

    # 3. Import files
    print(f"Importing files from {GCS_PATH}...")
    resp = rag.import_files(
        corpus_name=corpus.name,
        paths=[GCS_PATH],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
        ),
        llm_parser=rag.LlmParserConfig(
            model_name="gemini-2.5-flash",
            custom_parsing_prompt=PARSING_PROMPT
        ),
    )
    print(f"Import finished! Imported {getattr(resp, 'imported_rag_files_count', 'N/A')} files.")
    return corpus.name

if __name__ == "__main__":
    create_and_index()
