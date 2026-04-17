import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
from crewai.tools import BaseTool
from tavily import TavilyClient

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide")

# --- 2. CUSTOM CSS (Kellton Luxe UI 4.0) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #030303;
    }

    /* Nagłówek główny - zacieśniony */
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 82px !important;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: -28px !important;
        letter-spacing: -4px;
        line-height: 1;
    }

    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 52px !important;
        letter-spacing: 4px !important;
        color: #FC64FF;
        display: block;
        margin-bottom: 4rem;
    }

    .section-label {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 28px !important;
        letter-spacing: 3px !important;
        color: #49E1DD;
        margin-bottom: 1.5rem !important;
        display: block;
    }

    /* Prawa kolumna - Gradientowy grafit */
    [data-testid="column"]:nth-of-type(2) {
        background: linear-gradient(160deg, #16161A 0%, #050505 100%) !important;
        border-left: 1px solid rgba(255,255,255,0.08) !important;
        padding: 50px !important;
        min-height: 100vh;
    }

    /* Pola tekstowe - KONIEC Z CZERWONYM FOCUSEM */
    .stTextArea textarea, .stTextInput input {
        background-color: #0F0F11 !important;
        border: 1px solid #2A1F5C !important;
        border-radius: 16px !important;
        color: #FFFFFF !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #FC64FF !important;
        box-shadow: 0 0 15px rgba(252, 100, 255, 0.4) !important;
        outline: none !important;
    }

    /* Przycisk */
    .stButton>button {
        background: linear-gradient(90deg, #452DA2 0%, #FC64FF 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* KARTA WYNIKU - Biała z gradientową ramką */
    .result-card {
        background: #FFFFFF !important;
        color: #1A1A1A !important;
        padding: 35px;
        border-radius: 24px;
        margin-bottom: 30px;
        position: relative;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        border: 2px solid transparent;
    }
    
    .result-card::before {
        content: '';
        position: absolute;
        top: -2px; bottom: -2px; left: -2px; right: -2px;
        background: linear-gradient(90deg, #452DA2, #FC64FF);
        z-index: -1;
        border-radius: 26px;
    }

    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. PIN LOGIC ---
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

# --- 4. HISTORY FUNCTIONS (Muszą być TU!) ---
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

# --- 5. LOAD KEYS & TOOLS ---
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

# --- 6. AGENTS ---
kellton_brand_voice = """
Identity: Kellton Europe. Results-oriented, casual but sharp. 
Style: Active voice, use contractions, no fluff.
Banned: synergy, leverage, game-changing, revolutionary, utilize, delve, etc.
Constraint: No "Not just X, but Y". Use spaced en-dash ( – ).
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
    goal='Write sharp LinkedIn posts based strictly on research.',
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

# --- 7. APP LAYOUT ---
# Pasek boczny
st.sidebar.markdown('<p class="section-label" style="font-size: 24px !important;">📚 Archive</p>', unsafe_allow_html=True)
hist_df = load_history()
if not hist_df.empty:
    st.sidebar.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
    st.sidebar.download_button("📥 DOWNLOAD CSV", data=hist_df.to_csv(index=False).encode('utf-8-sig'), file_name="kellton_plan.csv", mime="text/csv")

# Nagłówek
st.markdown('<h1 class="main-title">KELLTON EUROPE</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">Social Media Specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('<p class="section-label">What are we writing about today?</p>', unsafe_allow_html=True)
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    st.markdown('<p class="section-label">Result</p>', unsafe_allow_html=True)
    
    if btn and temat:
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Processing Batch {index + 1}...'):
                rok = datetime.now().year
                t0 = Task(description=f"Find {rok} news on: '{pojedynczy_temat}'.", expected_output="Facts/URLs.", agent=researcher)
                t1 = Task(description="Write LinkedIn post. Brand voice.", expected_output="Post text.", agent=copywriter)
                t2 = Task(description="Midjourney prompt for this post.", expected_output="Prompt string.", agent=art_director)
                
                crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                crew.kickoff()
                
                post_text = getattr(t1.output, 'raw_output', str(t1.output))
                visual_prompt = getattr(t2.output, 'raw_output', str(t2.output))
                
                save_to_history(pojedynczy_temat, f"{post_text}\n\nPrompt: {visual_prompt}")
                
                clean_post = post_text.replace('\n', '<br>')
                
                st.markdown(f'''
                    <div class="result-card">
                        <div style="font-weight: 800; color: #452DA2; font-size: 14px; letter-spacing: 1px; margin-bottom: 15px;">BATCH {index + 1} READY</div>
                        <div style="color: #1A1A1A; font-size: 16px; margin-bottom: 25px; font-weight: 400;">{clean_post}</div>
                        <div style="background: #F4F4F9; padding: 20px; border-radius: 12px; border-left: 4px solid #FC64FF;">
                            <strong style="color: #000; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">📸 Visual Prompt</strong><br>
                            <span style="color: #444; font-size: 14px; font-style: italic;">{visual_prompt}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)

                with st.expander("🔍 Sources, please!"):
                    surowe_notatki = getattr(t0.output, 'raw_output', str(t0.output))
                    st.write(surowe_notatki)
