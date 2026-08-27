import os
import sys
import json
sys.path.insert(0, "/config/Desktop/BuildWithGemini/ai-fact-checker")

from google.genai import types
from google.genai.client import Client
from app.agent import root_agent

client = Client(vertexai=True)
model = "gemini-2.5-flash"
system_instruction = root_agent.instruction

print("Testing model directly with exact system instruction from agent...")

response = client.models.generate_content(
    model=model,
    contents="Show me the recent fact-checks in the catalog as a visual table. I have 1 fact check: Claim: Moon is cheese, Verdict: FALSE, Confidence: 100",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
    ),
)
print("Model output:", response)
