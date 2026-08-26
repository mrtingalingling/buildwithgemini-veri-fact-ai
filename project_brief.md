# My agent: AI Fact-Checker & Hallucination Detector
One-liner: A conversational agent that helps users fact-check claims and AI outputs with a catalog of verified sources, source quality metrics, and a calculated hallucination likelihood.

Tool coverage:
- Memory: Remembers the user's core query, identifies the factual claims within it, and tracks the investigative conversation (including user biases identified via open-ended probing).
- Tools: Google Search lookup for claim verification, secondary search for author/source credibility (date, author background, conflict of interest/implicit bias).
- Catalog/UI: A "Fact-Check Card" and data table displaying: Original Statement, Factual Likelihood (%), False/Hallucination Likelihood (%), Verdict, Number of Sources Referenced, and Cited Sources list.
- Image gen: n/a
- Sandbox: Runs a specific statistical algorithm/scoring heuristic to calculate the exact 'hallucination likelihood %' based on the weight and conflict of the fetched sources.

Core rails (everyone): memory, tools, eval, deploy, frontend
My stretch menu (pick later): A2UI (Catalog/UI), Code Sandbox
First eval question: "If I ask 'Did humans land on Mars in 2024?', the agent should challenge my premise, search for the claim, evaluate the sources (finding none credible), and return a Fact-Check table with a 99%+ Hallucination Likelihood."
