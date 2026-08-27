# VeriFact AI: User Journeys

## Journey 1: Standard Fact-Checking Workflow (Web UI)
1. **Input**: The user opens the PWA or Web UI and enters a claim (e.g., "Is the earth flat?") into the chat input.
2. **Bias Check**: The agent responds with a conversational, open-ended question to prompt the user to think about their bias before proceeding.
3. **Verification**: The user answers the prompt. The agent acknowledges the response, then calls the Google Search tool and the Source Credibility tool in the background.
4. **Scoring**: The agent uses the Sandbox tool to run a script that calculates exact Hallucination, Accuracy, and Falsehood percentages.
5. **Presentation**: The agent replies with friendly, conversational prose summarizing the findings. Immediately below, it renders the A2UI Fact Catalog Grid—a visually structured table containing the claim, verdict, and the three confidence metrics.
6. **Fact Management**: The user opens the "Fact Catalog" tab in the sidebar, reviews the saved claim, and toggles it "ON" so the agent remembers it as a grounded fact for future sessions.

## Journey 2: Chrome Extension Web Scanning
1. **Activation**: The user installs the extension and navigates to a news article.
2. **Permissions**: A popup requests permission to read the page content for a specified duration.
3. **DOM Scanning**: Upon approval, the extension extracts the page text and sends it to the VeriFact backend.
4. **Processing**: The backend agent identifies claims and calculates confidence scores (Accuracy, Falsehood, Hallucination) for each.
5. **Highlighting**: The extension injects CSS to highlight claims on the page:
   - Green (High Accuracy Confidence)
   - Yellow (Uncertain / Mixed Sources)
   - Red (High Falsehood/Hallucination Confidence)
6. **Interaction**: The user hovers over a highlighted sentence. A WOT-style tooltip appears, explaining the verdict and listing cited sources.

## Journey 3: Frictionless "Without Cap" Upgrade
1. **Cap Reached**: The user asks their 16th query of the day. The agent intercepts the request and responds with a friendly note that the daily cap has been reached.
2. **Prompt**: The agent presents a "Continue without cap" button, explaining they can bring their own model (Gemini, Claude, or OpenAI).
3. **Frictionless Auth**: Instead of hunting for API keys on developer portals, the user clicks the button and is presented with a simplified OAuth-style login or secure connection flow.
4. **Resumption**: Once authenticated, the 16th query is processed using the user's connected account, and the daily cap is permanently lifted.

## Journey 4: Global Truth Pool Sharing
1. **Personalization**: A user corrects the agent on a highly specific domain topic, and the agent saves this custom fact to their isolated personal Memory Bank.
2. **Validation**: Over time, the user realizes this fact is universally applicable. They go to the Fact Catalog UI and click "Share to Global Pool".
3. **Availability**: The fact is merged into the shared Firestore/Memory Bank.
4. **Community Reference**: Another user asks a related question, and the agent references the newly promoted fact, explicitly noting that it was sourced from the community knowledge pool.
