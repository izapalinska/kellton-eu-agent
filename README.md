# ⚡ Kellton EU Agent: Social Media Assistant
> **A high-performance AI orchestration system designed to research, write, and direct visual content for B2B brands.**

---

## The vision
Modern marketing demands high-frequency, high-quality content, but AI-generated text often feels corporate and hollow (and even more cringe than my beloved dad jokes). I built the **Kellton EU Social Media Assistant** to bridge this gap. It's a virtual squad that enforces strict brand-voice constraints and integrates real-time market data to ensure every post is grounded in current reality.

## 🧠 The solution (How it works)
The system uses an **Agentic Workflow**. Instead of one prompt, you have four specialized agents checking each other's work:

### 🔄 The pipeline:
1.  **The Senior Researcher:** Takes a raw topic and uses **Tavily Web Search** to find real-time data and news. No AI hallucinations — only facts.
2.  **The Lead Strategist:** Receives the research and applies the **Kellton Brand Voice**. It uses Negative Constraints (a LOT of them XD) to surgically remove corporate buzzwords (no "synergy," no "chess/jazz" metaphors, no classic "It's not... it's..." BS). Is it perfect? By no means, no. Friendly reminder that HUMAN LINGUISTIC QA WILL NEVER BE DEAD *thankyouverymuch*
3. **The Ruthless Editor:** The "no bullshit" filter. This agent aggressively cuts jargon, fixes rhythm, and ensures we're using active voice and contractions. If it sounds like a PowerPoint, the Editor kills it with fire.
4.  **The Art Director:** Generates high-quality visual prompts for Midjourney/Nano Banana OR directs the internal graphic engine.
5.  **The Content Vault:** All generated content is automatically logged into a persistent CSV database for historical tracking.

## 🛠️ The tech stack
* **Orchestration framework** - `CrewAI` (Managing the collaboration between Agents).
* **Brain power** - `OpenAI GPT-5-mini` (Advanced reasoning and voice adherence).
* **Search intelligence** - `Tavily AI` (Enterprise-grade web search for LLMs).
* **Interface** - `Streamlit` (A custom-built Python web dashboard).
* **Data management** - `Pandas` (For the history and archival system).
* **Graphics** – `Pillow` (On-the-fly PNG generation for quote cards).

## Key features from the perspective of a content manager
* **Multi-format support:** Choose between **Standard Posts, Carousels, LinkedIn Polls, or Case Studies**. The system adjusts the structure automatically.
* **Research toggle:** Want a post based *only* on your thoughts? Turn off web research with one click.
* **Instant visuals:** Generate ready-to-use PNG quote cards directly in the app. No need to open Canva for a simple insight.
* **Source transparency:** Every researched post comes with a "Sources, please!" section so you can verify the data.
* **Anti-AI filter:** Hard-coded ban on words like *synergy, leverage, paradigm shift,* and *revolutionary*.

*Built with Python and a passion for procrastination*
