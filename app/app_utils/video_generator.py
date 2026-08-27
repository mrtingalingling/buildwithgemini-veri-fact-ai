import base64
import os
import random
from typing import Any
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

BUCKET_NAME = "ai-fact-checker-assets-qwiklabs-gcp-04-6fd860cf790f"
PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"

async def generate_fact_check_video(topic: str, tool_context: ToolContext) -> dict[str, Any]:
    """Generates a short educational video summarizing or debunking a claim or topic.

    Args:
        topic: The claim or topic to generate a video for (e.g., "The Earth is flat", "Humans landed on Mars in 2024").
        tool_context: The execution context containing state and artifact services.

    Returns:
        A dictionary containing the public GCS URL of the generated video and success status.
    """
    try:
        # Configure env variables for Google Gen AI SDK to target Enterprise globally
        os.environ["GOOGLE_GENAI_USE_ENTERPRISE"] = "True"
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
        os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID

        # Initialize the Google Gen AI client
        client = genai.Client()
        
        prompt = (
            f"An educational cinematic scene debunking or verifying the claim: '{topic}'. "
            "Clean professional visual sequence, explanatory motion graphics."
        )

        # Call the Omni model (gemini-omni-flash-preview) to generate the video
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt
        )

        if not interaction.output_video or not interaction.output_video.data:
            return {"status": "error", "message": "The video generation model returned an empty response."}

        # Decode video bytes from base64
        video_bytes = base64.b64decode(interaction.output_video.data)

        # 1. Save artifact so it shows up in Playground's Artifacts panel
        part = types.Part(inline_data=types.Blob(mime_type="video/mp4", data=video_bytes))
        rand_suffix = random.randint(1000, 9999)
        artifact_name = f"fact_check_video_{rand_suffix}.mp4"
        await tool_context.save_artifact(artifact_name, part)

        # 2. Upload video bytes to public GCS bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        
        # Convert topic to a safe filename
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic.lower())[:30]
        gcs_filename = f"videos/fact_check_{safe_topic}_{rand_suffix}.mp4"
        blob = bucket.blob(gcs_filename)
        
        # Upload directly from bytes (no local file writing)
        blob.upload_from_string(video_bytes, content_type="video/mp4")
        
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_filename}"

        return {
            "status": "success",
            "message": f"Successfully generated a cinematic fact-check video for '{topic}'.",
            "artifact_name": artifact_name,
            "public_url": public_url
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
