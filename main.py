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

# --- CUSTOM CSS (Kellton Luxe UI 3.0) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Instrument+Serif:ital@0;1&display=swap');

    /* Fundament */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #050505;
    }

    .main {
        background-color: #050505;
    }

    /* Nagłówek główny - Większy i z oddechem */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 64px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin-top: 2rem;
        margin-bottom: 0.5rem;
        letter-spacing: -2px;
        line-height: 1;
    }

    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 32px;
        color: #FC64FF; /* Neonowy akcent Kellton */
        margin-bottom: 2rem;
        display: block;
    }

    .section-label {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 24px;
        color: #49E1DD; /* Neonowy cyjan Kellton */
        margin-bottom: 1rem;
        opacity: 0.9;
    }

    /* Lewa kolumna - Czysta i przestronna */
    [data-testid="column"]:nth-of-type(1) {
        padding: 3rem !important;
    }

    /* Prawa kolumna - Wyraźnie oddzielona z brandowym tłem */
    [data-testid="column"]:nth-of-type(2) {
        background: linear-gradient(180deg, #0A081B 0%, #050505 100%);
        border-left: 1px solid rgba(69, 45, 162, 0.3);
        padding: 3rem !important;
        min-height: 100vh;
    }

    /* Pola tekstowe - Sleek & Glow */
    .stTextArea textarea {
        background-color: #0F0F11 !important;
        border: 1px solid #1F1F22 !important;
        border-radius: 16px !important;
        color: #FFFFFF !important;
        padding: 20px !important;
        font-size: 16px !important;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #452DA2 !important;
        box-shadow: 0 0 20px rgba(69, 45, 162, 0.2) !important;
    }

    /* Przycisk - Powrót gradientu i cienia */
    .stButton>button {
        background: linear-gradient(90deg, #452DA2 0%, #FC64FF 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 15px 30px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 10px 30px rgba(252, 100, 255, 0.3);
        transition: all 0.3s ease !important;
        margin-top: 1rem;
    }
    
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(252, 100, 255, 0.5);
    }

    /* Glassmorphism w wynikach */
    .stAlert {
        background-color: rgba(18, 18, 20, 0.6) !important;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 20px !important;
        padding: 30px !important;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }

    /* Poprawa widoczności źródeł */
    .streamlit-expanderHeader {
        background-color: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP LAYOUT ---
st.markdown('<h1 class="main-title">My little junior</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">SoMe specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('<p class="section-label">What are we writing about today?</p>', unsafe_allow_html=True)
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)
    # Tu leci Twoja pętla z wynikami (if btn and temat...)

# --- PIN LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Good to see you, sis!")
    pin = st.text_input("Enter your access PIN:", type="password")
    if st.button("Enter"):
        if pin == "4014": # ZMIEŃ NA SWÓJ PIN
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.stop()

# --- LOAD KEYS ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

# --- HISTORY ---
FILE_NAME = "post_history.csv"
def save_to_history(topic, content):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.DataFrame([[now, topic, content]], columns=['Date', 'Topic/Notes', 'Generated Content'])
    if not os.path.isfile(FILE_NAME):
        df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')

def load_history():
    if os.path.isfile(FILE_NAME):
        return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    return pd.DataFrame(columns=['Date', 'Topic/Notes', 'Generated Content'])

# --- TOOLS ---
class CustomTavilySearchTool(BaseTool):
    name: str = "Tavily Web Search"
    description: str = "Search the web for the latest information and news."
    def _run(self, search_query: str) -> str:
        try:
            client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
            response = client.search(query=search_query, max_results=4)
            results = response.get("results", [])
            if results:
                return "\n\n".join([f"Link: {r.get('url', '')}\nSnippet: {r.get('content', '')}" for r in results])
            return "No results."
        except Exception as e:
            return f"Search failed: {str(e)}"

search_tool = CustomTavilySearchTool()
scrape_tool = ScrapeWebsiteTool()

# --- AGENTS (Twoje instrukcje) ---
# Tutaj upewnij się, że wkleiłaś swoje wyedytowane instrukcje Kellton
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
    goal='Search the web for the latest data and trends.',
    backstory='You are a sharp B2B tech researcher. You translate topics into punchy English queries.',
    verbose=True,
    tools=[search_tool]
)

copywriter = Agent(
    role='Lead Content Strategist',
    goal='Write sharp LinkedIn posts based strictly on research.',
    backstory=kellton_brand_voice,
    verbose=True,
    tools=[scrape_tool]
)

art_director = Agent(
    role='Art Director',
    goal='Generate ONE Midjourney prompt.',
    backstory="You stick to the Kellton Europe KV. Use negative space.",
    verbose=True
)

# --- APP LAYOUT ---
st.markdown('<h1 class="main-title">My little junior</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">SoMe specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('<p class="section-label">What are we writing about today?</p>', unsafe_allow_html=True)
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)
    if btn and temat:
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        st.write(f"I'm working: {len(lista_tematow)} queued posts.")
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Processing {index + 1}...'):
                rok = datetime.now().year
                t0 = Task(description=f"Search for {rok} news on: '{pojedynczy_temat}'. Must include URLs.", expected_output="Facts and Sources.", agent=researcher)
                t1 = Task(description="Write LinkedIn post based on research. Brand voice.", expected_output="Post text.", agent=copywriter)
                t2 = Task(description="Generate Midjourney prompt based on post.", expected_output="Prompt string.", agent=art_director)
                
                crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                crew.kickoff()
                
                # Wyciąganie wyników
                p = getattr(t1.output, 'raw_output', str(t1.output))
                m = getattr(t2.output, 'raw_output', str(t2.output))
                res = f"{p}\n\n---\n📸 **Visual Design Prompt:**\n{m}"
                
                save_to_history(pojedynczy_temat, res)
                st.success(f"Batch {index+1} ready!")
                st.info(res)
                with st.expander("🔍 Sources, please!"):
                    st.write(getattr(t0.output, 'raw_output', str(t0.output)))
