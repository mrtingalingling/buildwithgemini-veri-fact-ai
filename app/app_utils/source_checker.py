import aiohttp

async def check_source_credibility(entity: str) -> dict:
    """Fetches background, credibility, and authority information on a source, publication, or author from Wikipedia.

    Args:
        entity: The name of the author, publication, media outlet, or organization (e.g., 'Reuters', 'BBC').

    Returns:
        A dictionary containing the entity summary, description, and URL.
    """
    formatted_entity = entity.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted_entity}"
    headers = {"User-Agent": "AIFactCheckerAgent/1.0"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "title": data.get("title"),
                        "description": data.get("description"),
                        "summary": data.get("extract"),
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                    }
                return {
                    "status": "not_found",
                    "message": f"No background entry found for '{entity}'.",
                }
    except Exception as e:
        return {"status": "error", "message": f"Failed to check credibility for '{entity}': {str(e)}"}
