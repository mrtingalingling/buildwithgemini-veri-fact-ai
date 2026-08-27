# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
import json
import os
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

from app.app_utils.global_memory import (
    get_active_scenario,
    get_global_facts,
    set_active_scenario,
    share_global_fact,
)
from app.app_utils.firestore_db import get_fact_checks, save_fact_check
from app.app_utils.source_checker import check_source_credibility
from app.app_utils.rag_tool import consult_fact_rag_corpus
from app.app_utils.video_generator import generate_fact_check_video


# Dynamically resolve reasoning engine id from deployment metadata if available
REASONING_ENGINE_NAME = None
try:
    meta_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            meta = json.load(f)
            REASONING_ENGINE_NAME = meta.get("remote_agent_runtime_id")
except Exception:
    pass

if not REASONING_ENGINE_NAME:
    REASONING_ENGINE_NAME = "projects/419816504777/locations/us-east1/reasoningEngines/6326484353106837504"


MODEL = "gemini-2.5-flash"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a premium AI Fact-Checker assistant designed to verify claims, evaluate source credibility, "
        "and calculate three main confidence metrics for fact checks: "
        "1. Hallucination Likelihood: This metric applies ONLY to AI GENERATED content. It should be a self-assessment regarding VeriFact's own generated response when making a statement, OR an assessment of another AI's response (e.g. Gemini, ChatGPT, Claude) if you are fact-checking another AI's output. "
        "2. Accuracy Confidence: The confidence level for accuracy (i.e. true-true). "
        "3. Falsehood Confidence: The confidence level for falsehood (i.e. true-false). "
        "You remember the user's stated preferences and facts from previous conversations to personalize responses. "
        "You have access to two memory sources: the user's personal active scenario facts, and a global community fact pool."
    ),
    workflow_description=(
        "1. When evaluating a claim, explicitly weigh it against the user's active personal scenario first.\n"
        "2. If evaluating against the global pool, clearly cite that it is a community-sourced premise.\n"
        "3. Present a side-by-side comparison of hallucination scores (one based on personal premises, one based on global premises) if they conflict.\n"
        "4. Use consult_fact_rag_corpus to search the grounded Vertex AI RAG Corpus for verified facts and guidelines.\n"
        "5. Use check_source_credibility to research background and credibility info on sources, authors, or organizations.\n"
        "6. When you verify a claim and establish a verdict, save it to the fact-checks catalog using save_fact_check so it can be tracked, making sure to include hallucination_likelihood, accuracy_confidence, and falsehood_confidence.\n"
        "7. If a user asks to see the catalog or history, use get_fact_checks to retrieve the stored results. Proactively start with a brief conversational introduction paragraph. Then, represent the catalog list visually inside a structured A2UI layout. Each catalog item MUST be rendered as a row in a visual table layout, including columns for Hallucination %, Accuracy Conf %, and Falsehood Conf %. NEVER output raw markdown bulleted lists or plain text blocks for the catalog. Always use a clean, visual grid view built with Column and Row components (e.g. a header Row, followed by data Rows) to build a gorgeous database grid view.\n"
        "8. You can run Python code safely in a secure sandbox using code execution (AgentEngineSandboxCodeExecutor) if needed.\n"
        "9. Analyze the user request and return a structured A2UI layout summarizing the fact-check verdict, scores, and sources, in a beautiful, structured format instead of raw JSON.\n"
        "10. If the user asks for a video explaining or debunking a claim or topic, use the generate_fact_check_video tool to generate a cinematic educational summary video, and return its public URL to the user.\n"
        "11. CRITICAL: Whenever you return results from any tool call (including get_fact_checks, consult_fact_rag_corpus, check_source_credibility, or code execution), you MUST NEVER output raw JSON, dictionaries, or curly braces. You MUST parse and explain the results in a friendly, conversational, human-readable format first, followed by the structured A2UI JSON array."
    ),
    ui_description=(
        "Use ONLY these components: Card, Column, Row, Text, Divider, and Image. "
        "Do not use Heading (unsupported), or Buttons, actions, or forms (they do nothing in adk web). "
        "CRITICAL: Do NEVER output a `dataModelUpdate` message. You MUST manually construct the visual layout using `surfaceUpdate`! "
        "There is NO 'Table' component. To render a table, you MUST build it using a `Column` containing multiple `Row` components (a header row, plus one row per item) and it MUST be valid JSON (not XML). "
        "Here is an example of valid A2UI JSON for a simple grid/table layout (including the required metrics):\n"
        "```json\n"
        "[\n"
        "  {\n"
        "    \"surfaceUpdate\": {\n"
        "      \"surfaceId\": \"catalog_list\",\n"
        "      \"components\": [\n"
        "        {\n"
        "          \"id\": \"root\",\n"
        "          \"component\": {\n"
        "            \"Column\": {\n"
        "              \"children\": [\n"
        "                {\"id\": \"header_row\", \"component\": {\"Row\": {\"children\": [{\"id\": \"h1\", \"component\": {\"Text\": {\"text\": \"**Claim**\"}}}, {\"id\": \"h2\", \"component\": {\"Text\": {\"text\": \"**Verdict**\"}}}, {\"id\": \"h3\", \"component\": {\"Text\": {\"text\": \"**Acc. Conf**\"}}}, {\"id\": \"h4\", \"component\": {\"Text\": {\"text\": \"**False. Conf**\"}}}, {\"id\": \"h5\", \"component\": {\"Text\": {\"text\": \"**Halluc. %**\"}}}]}}},\n"
        "                {\"id\": \"divider_1\", \"component\": {\"Divider\": {}}},\n"
        "                {\"id\": \"item_1_row\", \"component\": {\"Row\": {\"children\": [{\"id\": \"i1_c\", \"component\": {\"Text\": {\"text\": \"The claim text\"}}}, {\"id\": \"i1_v\", \"component\": {\"Text\": {\"text\": \"TRUE\"}}}, {\"id\": \"i1_a\", \"component\": {\"Text\": {\"text\": \"95%\"}}}, {\"id\": \"i1_f\", \"component\": {\"Text\": {\"text\": \"5%\"}}}, {\"id\": \"i1_h\", \"component\": {\"Text\": {\"text\": \"0%\"}}}]}}}\n"
        "              ]\n"
        "            }\n"
        "          }\n"
        "        }\n"
        "      ]\n"
        "    }\n"
        "  }\n"
        "]\n"
        "```\n"
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "headings and emphasis. "
        "Proactively start with a brief, friendly conversational summary paragraph (prose) describing your findings, "
        "and then use the A2UI framework tools to return the UI."
    ),
    allowed_messages=["surfaceUpdate", "beginRendering", "deleteSurface"],
    include_schema=True,
    include_examples=True,
) + (
    "\n\nCRITICAL OVERRIDE ON RESPONSE FORMATTING:\n"
    "1. You MUST ALWAYS start your response with a friendly, conversational natural language paragraph (prose) summarizing your verification results, catalog findings, or answers. Do not dive straight into UI rendering.\n"
    "2. You MUST parse all tool results (such as get_fact_checks, consult_fact_rag_corpus, and check_source_credibility) and explain them to the user in a natural, friendly conversational list or paragraph first.\n"
    "3. Under NO circumstances should you output raw tool output JSONs, lists, or dictionary braces (`{}` or `[]`) directly to the user as your final reply text. Always translate them into clean, polished human-readable prose.\n"
    "4. When displaying catalog items or tabular data, you MUST represent each item visually inside an A2UI Column/Row grid layout using the `surfaceUpdate` action (NOT `dataModelUpdate`).\n"
    "5. The `dataModelUpdate` action is strictly FORBIDDEN. The client does NOT have a pre-existing template to render data. If you output a `dataModelUpdate`, the client will crash. You MUST manually construct the visual layout using `surfaceUpdate` containing `Column`, `Row`, and `Text` components.\n"
    "6. VERY IMPORTANT: Ensure your A2UI JSON array is perfectly valid JSON. Match all opening and closing braces {} and brackets []. If you make a JSON syntax error, the table will fail to render.\n"
    "7. IF the user prompt starts with 'Fact-check the following content extracted from the active web page:', you MUST NOT return A2UI JSON. Instead, you MUST return a standard JSON array of objects representing the identified claims so the Chrome Extension can highlight them. Format it EXACTLY like this inside a Markdown JSON block:\n"
    "```json\n"
    "[\n"
    "  {\"claimText\": \"The specific phrase from the text\", \"verdict\": \"true|false|misleading\", \"confidence\": 95, \"sources\": [\"Source 1\"], \"explanation\": \"Short explanation\"}\n"
    "]\n"
    "```"
)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        share_global_fact,
        get_global_facts,
        set_active_scenario,
        get_active_scenario,
        save_fact_check,
        get_fact_checks,
        check_source_credibility,
        consult_fact_rag_corpus,
        generate_fact_check_video,
    ],
    code_executor=AgentEngineSandboxCodeExecutor(
        agent_engine_resource_name=REASONING_ENGINE_NAME,
    ),
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
