# VeriFact AI Features

## 1. Core Agent Capabilities
- **Intelligent Fact-Checking**: The agent parses user queries to identify specific factual claims, interrogates the user to surface biases, and independently researches the claims.
- **Three Confidence Metrics**:
  - *Accuracy Confidence*: Percentage likelihood that a claim is completely true (true-true).
  - *Falsehood Confidence*: Percentage likelihood that a claim is completely false (true-false).
  - *Hallucination Likelihood*: (Specific to AI-generated content) Likelihood that the AI hallucinated the information.
- **Source Verification**: Performs secondary searches to evaluate source credibility, author background, date, and potential conflicts of interest.
- **Code Sandbox Evaluation**: Uses a secure Python Sandbox to run a custom statistical heuristic, calculating exact confidence percentages based on source weights.

## 2. Memory & Context Architecture
- **Personalized Fact Bank**: Facts submitted by a user are stored in isolation and marked factual *only* for that user.
- **Context Toggles (NotebookLM-Style)**: Users can toggle specific facts on or off in their personal bank, changing the agent's baseline assumptions.
- **Global Truth Pool**: Validated facts can be promoted to a shared pool accessible by all users for reference.
- **Vertex AI RAG Integration**: Users can upload files (PDFs, docs) to ground the agent's answers.

## 3. UI/UX & Output Formatting
- **Visual Data Grid**: Uses A2UI (Agent-to-UI) to render the "Fact Catalog" as a beautiful, interactive, tabular grid containing all claims, verdicts, and calculated metrics.
- **Exclusive Tabbed Views**: The "Sources" and "Fact Catalog" sections operate as toggleable tabs in the sidebar, displaying only one at a time.
- **Conversational Tone**: The agent never dumps raw JSON. It always introduces data with friendly prose before rendering visual tables.

## 4. Platform Integrations
- **Progressive Web App (PWA)**: The web UI is fully installable as a mobile-like desktop and mobile app.
- **Chrome Extension Mode**: The app can be packaged as a browser extension.
  - **DOM Scanning & WOT Highlighting**: The extension requests page access, scans the active text, and applies traffic-light colors (Green/Yellow/Red) to claims with tooltips explaining the verdict and source.
- **Video Generation**: Generates cinematic educational summaries using the Gemini Omni model and saves them to a public Cloud Storage bucket.

## 5. Monetization & Authentication
- **15-Query Cap**: Free users are limited to 15 queries per day.
- **Frictionless "Bring Your Own Model" (BYOM)**: Users can upgrade to "without cap" access by authenticating and routing traffic through a simplified BYOM flow (supporting Gemini, Claude, OpenAI) without dealing with complex API keys.
