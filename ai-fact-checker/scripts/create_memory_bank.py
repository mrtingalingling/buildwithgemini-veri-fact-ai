import vertexai
import os

PROJECT_ID = "qwiklabs-gcp-04-6fd860cf790f"
LOCATION   = "us-central1"

print(f"Creating Memory Bank in {PROJECT_ID}/{LOCATION}...")
client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

# A Memory Bank instance IS an Agent Engine instance. Default config is fine
# for the lab; it extracts general user facts/preferences automatically.
memory_bank = client.agent_engines.create()

resource_name = memory_bank.api_resource.name       # projects/.../reasoningEngines/NNN
memory_bank_id = resource_name.split("/")[-1]        # NNN  <- use this everywhere
print("MEMORY_BANK_ID:", memory_bank_id)
print("resource name :", resource_name)

# Save the ID to a file for later steps
with open("memory_bank_id.txt", "w") as f:
    f.write(memory_bank_id)
