import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
from crewai.tools import BaseTool
from tavily import TavilyClient

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide")

# --- CUSTOM CSS (Kellton Final Polish & Result Cards) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #030303;
    }

    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 82px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: -25px !important; /* Drastycznie mniejszy odstęp */
        letter-spacing: -4px;
    }

    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 52px !important; /* Większy subheader */
        letter-spacing: 4px !important; /* Większy spacing między literami */
        color: #FC64FF;
        display: block;
        margin-bottom: 3.5rem;
    }

    .section-label {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 28px !important; /* Mniejszy niż sub-nagłówek */
        letter-spacing: 3px !important; /* Większy spacing */
        color: #49E1DD;
        margin-bottom: 1rem !important;
    }

    /* Prawa kolumna - Gradientowy vibe */
    [data-testid="column"]:nth-of-type(2) {
        background: linear-gradient(160deg, #121217 0%, #050505 100%) !important;
        border-left: 1px solid rgba(255,255,255,0.05) !important;
        padding: 50px !important;
        min-height: 100vh;
    }

    /* KARTA WYNIKU - Biała z gradientową obwódką */
    .result-card {
        background: #FFFFFF !important;
        color: #000000 !important;
        padding: 30px;
        border-radius: 20px;
        margin-bottom: 25px;
        position: relative;
        font-size: 16px;
        line-height: 1.6;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        border: 2px solid transparent;
        background-clip: padding-box;
    }
    
    /* Trick na gradientową obwódkę ramki */
    .result-card::before {
        content: '';
        position: absolute;
        top: -3px; bottom: -3px; left: -3px; right: -3px;
        background: linear-gradient(90deg, #452DA2, #FC64FF);
        z-index: -1;
        border-radius: 23px;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #FC64FF !important;
        box-shadow: 0 0 15px rgba(252, 100, 255, 0.4) !important;
    }
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- PIN LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<h1 class="main-title">Security <span style="font-family: \'Instrument Serif\'; font-style: italic; color: #FC64FF; font-size: 40px;">Check</span></h1>', unsafe_allow_html=True)
    pin = st.text_input("Enter your access PIN:", type="password")
    if st.button("Enter Access"):
        if pin == "4014": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.stop()

# --- LOAD KEYS & TOOLS ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

class CustomTavilySearchTool(BaseTool):
    name: str = "Tavily Web Search"
    description: str = "Search the web for the latest information and news."
    def _run(self, search_query: str) -> str:
        try:
            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            response = client.search(query=search_query, max_results=4)
            results = response.get("results", [])
            return "\n\n".join([f"Link: {r.get('url', '')}\nSnippet: {r.get('content', '')}" for r in results]) if results else "No results."
        except Exception as e:
            return f"Search failed: {str(e)}"

search_tool = CustomTavilySearchTool()
scrape_tool = ScrapeWebsiteTool()

# --- AGENTS ---
kellton_brand_voice = """
Identity: Kellton Europe, a trusted digital transformation partner for mid-to-large enterprises. We deliver enterprise-grade expertise with the heart and agility of a true partner. Our Message: The results you need. The partnership you want.
    Audience: Pragmatic, results-oriented senior leaders (CTO, CIO, CEO) who hate fluff and buzzwords.
    Be Casual: Write as you talk. Use contractions (it’s, we’ll, you’re). If it sounds stiff, rewrite it.
    Be Confident: Use strong, declarative sentences. Take a clear stance. Do not hedge with "might" or "perhaps".
    Active Voice Only: Say "We build apps," not "Apps are built by us".
    Lead with Benefits: Start with what the reader gets, not a list of features.
    Conversational Punctuation: Use a spaced en-dash ( – ) for pauses or emphasis – just like this. Start sentences with 'And' or 'But' if it helps the flow.
    Hooks and CTAs: Use strong hooks and engaging questions or CTAs.
    Banned: NEVER use these words: Synergy, leverage (as a verb), paradigm shift, game-changing, revolutionary, utilize, actionable insights, low-hanging fruit, circle back, touch base, embark, delve, plethora, multitude, testament to, cutting-edge, future-proof, robust, seamless, state-of-the-art.
    Constraint: No "Not just X, but Y". Use spaced en-dash ( – ).
    No AI-isms: Avoid "In the rapidly evolving world of..." or "delving into the intricacies of...". 
    Strict Style Constraint: Never use the "Not just X, but Y" or "It's not only about X, it's about Y" framing. Avoid any rhetorical device that tries to create a false contrast or "elevate" a concept by dismissing a simpler version of it. State facts directly.

"""

researcher = Agent(
    role='Senior Market Researcher',
    goal='Search for 2026 data and trends.',
    backstory='Sharp B2B researcher. Translates topics into English queries.',
    verbose=True,
    tools=[search_tool]
)

copywriter = Agent(
    role='Lead Content Strategist',
    goal='Write LinkedIn posts based strictly on research.',
    backstory=kellton_brand_voice,
    verbose=True,
    tools=[scrape_tool]
)

art_director = Agent(
    role='Art Director',
    goal='Generate ONE Midjourney prompt.',
    backstory="Kellton Europe KV style. Use negative space.",
    verbose=True
)

# --- APP LAYOUT (The Master Version) ---

# 1. PRZYWRACAMY ARCHIWUM (SIDEBAR)
st.sidebar.markdown('<p class="section-label" style="font-size: 24px !important;">📚 Archive</p>', unsafe_allow_html=True)
hist_df = load_history()
if not hist_df.empty:
    st.sidebar.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
    st.sidebar.download_button(
        label="📥 DOWNLOAD CSV",
        data=hist_df.to_csv(index=False).encode('utf-8-sig'),
        file_name="kellton_content_plan.csv",
        mime="text/csv"
    )

# 2. NAGŁÓWEK GŁÓWNY (Zacieśniony odstęp)
st.markdown('<h1 class="main-title">KELLTON EUROPE</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">Social Media Specialist</span>', unsafe_allow_html=True)

# 3. KOLUMNY
col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('<p class="section-label">What are we writing about today?</p>', unsafe_allow_html=True)
    # label_visibility="collapsed" usuwa systemowy napis nad polem
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)
    
    if btn and temat:
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        st.write(f"Working on {len(lista_tematow)} posts...")
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Agent is thinking (Batch {index + 1})...'):
                # LOGIKA CREWAI
                rok = datetime.now().year
                t0 = Task(description=f"Find {rok} insights for: '{pojedynczy_temat}'. Need URLs.", expected_output="Facts/Links.", agent=researcher)
                t1 = Task(description="Write LinkedIn post. Brand voice.", expected_output="Post text.", agent=copywriter)
                t2 = Task(description="Midjourney prompt for this post.", expected_output="Prompt string.", agent=art_director)
                
                crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                crew.kickoff()
                
                # ZBIERANIE WYNIKÓW
                post_text = getattr(t1.output, 'raw_output', str(t1.output))
                visual_prompt = getattr(t2.output, 'raw_output', str(t2.output))
                
                # Formatowanie do bazy danych (z zachowaniem nowej linii)
                res_to_save = f"{post_text}\n\nPrompt: {visual_prompt}"
                save_to_history(pojedynczy_temat, res_to_save)
                
                # WYŚWIETLANIE W BIAŁEJ KARCIE (Zamiast st.info)
                # Zamieniamy znaki nowej linii na <br> dla HTML
                clean_post = post_text.replace('\n', '<br>')
                
                st.markdown(f'''
                    <div class="result-card">
                        <div style="font-weight: 800; color: #452DA2; font-size: 14px; letter-spacing: 1px; margin-bottom: 15px;">
                            BATCH {index + 1} READY
                        </div>
                        <div style="color: #1A1A1A; font-size: 16px; margin-bottom: 20px;">
                            {clean_post}
                        </div>
                        <div style="background: #F8F8F8; padding: 15px; border-radius: 10px; border-left: 4px solid #FC64FF;">
                            <strong style="color: #000;">📸 Visual Prompt:</strong><br>
                            <span style="color: #444; font-size: 14px; font-style: italic;">{visual_prompt}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                with st.expander("🔍 Sources, please!"):
                    st.write(getattr(t0.output, 'raw_output', str(t0.output)))
