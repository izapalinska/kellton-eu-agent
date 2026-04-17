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

# --- CUSTOM CSS (Kellton Luxe UI 3.1 - The Final Fix) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #030303;
    }

    /* Główny kontener aplikacji */
    .stApp {
        background-color: #030303;
    }

    /* Nagłówek główny */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 72px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin-top: 1rem;
        margin-bottom: 0;
        letter-spacing: -3px;
    }

    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 38px;
        color: #FC64FF;
        margin-bottom: 3rem;
        display: block;
        text-shadow: 0 0 20px rgba(252, 100, 255, 0.3);
    }

    /* Znacznie większe nagłówki sekcji */
    .section-label {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 36px !important; /* Powiększone */
        color: #49E1DD;
        margin-top: 1rem;
        margin-bottom: 1.5rem !important;
        display: block;
    }

    /* Prawa kolumna - Wyraźne odcięcie */
    [data-testid="column"]:nth-of-type(2) {
        background-color: #0A081B !important;
        border-left: 2px solid rgba(69, 45, 162, 0.5) !important;
        padding: 40px !important;
        border-radius: 0 0 0 40px;
        box-shadow: -20px 0 40px rgba(0,0,0,0.5);
    }

    /* Pola tekstowe */
    .stTextArea textarea {
        background-color: #0F0F11 !important;
        border: 1px solid #2A1F5C !important;
        border-radius: 20px !important;
        color: #FFFFFF !important;
        padding: 24px !important;
        font-size: 18px !important;
    }

    /* Przycisk z mocnym glow */
    .stButton>button {
        background: linear-gradient(90deg, #452DA2 0%, #FC64FF 100%) !important;
        color: white !important;
        border-radius: 15px !important;
        padding: 18px 40px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        box-shadow: 0 0 30px rgba(252, 100, 255, 0.4) !important;
        border: none !important;
        width: 100%;
    }

    /* Wyniki - Glassmorphism */
    .stAlert {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 24px !important;
        padding: 30px !important;
        color: white !important;
    }
    
    /* Ukrycie śmieci Streamlita */
    header, footer {visibility: hidden;}
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

# --- APP LAYOUT (The Final One) ---
st.markdown('<h1 class="main-title">My little junior</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">SoMe specialist</span>', unsafe_allow_html=True)

# Szerokie kolumny z wyraźnym gapem
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
                
                p = getattr(t1.output, 'raw_output', str(t1.output))
                m = getattr(t2.output, 'raw_output', str(t2.output))
                res = f"{p}\n\n---\n📸 **Visual Design Prompt:**\n{m}"
                
                save_to_history(pojedynczy_temat, res)
                st.success(f"Batch {index+1} ready!")
                st.info(res)
                with st.expander("🔍 Sources, please!"):
                    st.write(getattr(t0.output, 'raw_output', str(t0.output)))
