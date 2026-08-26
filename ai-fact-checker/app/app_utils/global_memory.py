from google.genai import types
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.tools import ToolContext
from google.adk.tools import ToolContext
from app.app_utils.services import get_memory_service

GLOBAL_USER_ID = "global_community_pool"
GLOBAL_APP_NAME = "ai-fact-checker"

async def share_global_fact(fact: str) -> dict:
    """Shares a verified fact to the global community pool.
    
    Args:
        fact: The factual statement to share with the community.
    """
    ms = get_memory_service()
    if not ms:
        return {"status": "error", "message": "Memory service unavailable"}
    
    entry = MemoryEntry(content=types.Content(role="user", parts=[types.Part.from_text(text=fact)]))
    await ms.add_memory(
        app_name=GLOBAL_APP_NAME, 
        user_id=GLOBAL_USER_ID, 
        memories=[entry]
    )
    return {"status": "success", "message": f"Fact shared to global pool: {fact}"}

async def get_global_facts(query: str) -> dict:
    """Searches the global community memory pool for shared facts.
    
    Args:
        query: The topic or statement to search the global pool for.
    """
    ms = get_memory_service()
    if not ms:
        return {"status": "error", "message": "Memory service unavailable"}
        
    results = await ms.search_memory(
        app_name=GLOBAL_APP_NAME,
        user_id=GLOBAL_USER_ID,
        query=query
    )
    
    facts = []
    # results is a SearchMemoryResponse, which has 'memories' list
    for r in results.memories:
        if r.content and r.content.parts:
            facts.append(r.content.parts[0].text)
            
    return {"status": "success", "facts": facts}

async def set_active_scenario(scenario_name: str, premises: list[str], tool_context: ToolContext) -> dict:
    """Sets the active scenario and its premises for fact-checking.
    
    Args:
        scenario_name: Name of the scenario (e.g., 'default', 'what_if_mars_colony').
        premises: List of facts that are assumed to be true in this scenario.
    """
    tool_context.state["active_scenario"] = scenario_name
    tool_context.state["scenario_premises"] = premises
    return {"status": "success", "message": f"Active scenario set to {scenario_name}."}

async def get_active_scenario(tool_context: ToolContext) -> dict:
    """Gets the currently active scenario and its premises.
    """
    return {
        "active_scenario": tool_context.state.get("active_scenario", "default"),
        "scenario_premises": tool_context.state.get("scenario_premises", [])
    }
