import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
from crewai.tools import BaseTool
from tavily import TavilyClient

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- 2. HISTORY FUNCTIONS ---
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

# --- 3. CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #030303;
    }

    .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
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
        color: #FF66B2; 
        display: block;
        margin-bottom: 4rem;
    }

    [data-testid="column"]:nth-of-type(2) {
        background: linear-gradient(160deg, #16161A 0%, #050505 100%) !important;
        border-left: 1px solid rgba(255,255,255,0.08) !important;
        padding: 50px !important;
        min-height: 100vh;
    }

    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="base-input"] {
        background-color: #0F0F11 !important;
        border: 1px solid #2A1F5C !important;
        border-radius: 16px !important;
    }
    
    div[data-baseweb="input"]:focus-within > div, 
    div[data-baseweb="textarea"]:focus-within > div,
    div[data-baseweb="base-input"]:focus-within,
    .stTextArea textarea:focus, 
    .stTextInput input:focus {
        border-color: #A765FF !important;
        box-shadow: 0 0 0 1px #A765FF, 0 0 15px rgba(167, 101, 255, 0.4) !important;
        outline: none !important;
    }

    input, textarea {
        color: #FFFFFF !important;
        caret-color: #A765FF !important;
    }

    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #E31352 0%, #F86652 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(227, 19, 82, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(248, 102, 82, 0.6) !important;
    }
    div[data-testid="stButton"] > button::before, div[data-testid="stButton"] > button::after {
        display: none !important;
    }

    [data-testid="stDownloadButton"] button {
        background: linear-gradient(90deg, #E31352 0%, #F86652 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-weight: 800 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 15px rgba(227, 19, 82, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(248, 102, 82, 0.6) !important;
    }
    [data-testid="stDownloadButton"] button::before {
        content: '';
        display: inline-block;
        width: 18px;
        height: 18px;
        margin-right: 10px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23FFFFFF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 3v18h18'/%3E%3Cpath d='M18 9l-5 5-4-4-5 5'/%3E%3Cpath d='M18 9h-5'/%3E%3Cpath d='M18 9v5'/%3E%3C/svg%3E");
        background-size: cover;
    }

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
        background: linear-gradient(90deg, #A765FF, #FF66B2); 
        z-index: -1;
        border-radius: 26px;
    }
    
    [data-testid="stSidebar"] {
        background-color: #060514 !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    </style>
    """, unsafe_allow_html=True)

# --- 4. PIN LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<h1 class="main-title">Security <span style="font-family: \'Instrument Serif\'; font-style: italic; color: #A765FF; font-size: 40px; letter-spacing: 8px;">Check</span></h1>', unsafe_allow_html=True)
    pin = st.text_input("Enter your access PIN:", type="password")
    if st.button("Enter Access"):
        if pin == "4014": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.stop()

# --- 5. LOAD KEYS & TOOLS ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
# USTAWIONY GLOBALNY, NAJSZYBSZY SILNIK (Bez błędów walidacji!)
os.environ["OPENAI_MODEL_NAME"] = "gpt-4o"

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
ROLE AND IDENTITY: 
You are a sharp, skeptical, and highly experienced Tech Strategist at Kellton Europe. 
You hate "motivational" business talk. You value substance over style. 
You talk like someone who has seen 100 failed IT projects and knows exactly why they failed.

TONE & STYLE:
- No Metaphors: STRICTLY BAN comparisons to chess, checkers, sports, music, parties, or movies. 
- Blunt & Direct: If something is a trend, explain the cost or the risk. 
- Real Talk: Use contractions (it’s, don’t). Start sentences with "And" or "But".
- Use a spaced en-dash ( – ) for real pauses.

STRICT NEGATIVE CONSTRAINTS:
1. NO HYPE: Ban "VIP", "jazz", "chess", "checkers", "playbook", "underdogs", "strings", "sauce", "recipe".
2. NO CORPORATE BUZZWORDS: synergy, leverage, game-changing, revolutionary, robust, seamless, cutting-edge.
3. NO BINARY CONTRAST: Never use "Not just X, but Y". 
4. NO AI-ISMS: "In the rapidly evolving world", "shaking up", "beyond", "miss the bus".

EXAMPLES OF THE REAL KELLTON STYLE:
[BAD - Hype]: "Outsourcing is like a jazz quartet – smooth and innovatve."
[GOOD - Blunt]: "Most outsourcing fails because the incentives are wrong. In 2026, if you're still paying for hours instead of outcomes, you're literally funding your vendor's inefficiency."

[BAD - Cliché]: "Stop playing checkers and start playing chess with your strategy."
[GOOD - Blunt]: "Hiring an AI team isn't a strategy; it's a headcount move. The real strategy is knowing which parts of your legacy stack will actually survive the migration."
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

with st.sidebar:
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 20px; margin-bottom: 20px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="url(#docGrad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <defs><linearGradient id="docGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#A765FF" /><stop offset="100%" stop-color="#FF66B2" /></linearGradient></defs>
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 20px; letter-spacing: 1px; color: #A765FF;">Archive</span>
        </div>
    ''', unsafe_allow_html=True)
    
    hist_df = load_history()
    
    if not hist_df.empty:
        st.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
    else:
        st.markdown("<p style='font-family: \"Plus Jakarta Sans\", sans-serif; color: #888; font-size: 14px;'>Waiting for your first post...</p>", unsafe_allow_html=True)
        
    st.download_button(
        label="DOWNLOAD CSV", 
        data=hist_df.to_csv(index=False).encode('utf-8-sig'), 
        file_name="kellton_plan.csv", 
        mime="text/csv",
        use_container_width=True
    )

# WIDOK GŁÓWNY
st.markdown('<h1 class="main-title">KELLTON EUROPE</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">Social Media Specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#editGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <defs><linearGradient id="editGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#A765FF" /><stop offset="100%" stop-color="#FF66B2" /></linearGradient></defs>
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
            <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 24px; letter-spacing: 1px; color: #A765FF;">What are we writing about today?</span>
        </div>
    ''', unsafe_allow_html=True)
    
    temat = st.text_area("", height=300, placeholder="Np. Strategia AI w designie --- Trendy UX 2026", label_visibility="collapsed")
    btn = st.button("GET TO WORK, BRO")

with col2:
    st.markdown('''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.5rem;">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#chatGrad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <defs><linearGradient id="chatGrad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#A765FF" /><stop offset="100%" stop-color="#FF66B2" /></linearGradient></defs>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; font-size: 24px; letter-spacing: 1px; color: #A765FF;">Result</span>
        </div>
    ''', unsafe_allow_html=True)
    
    if btn and temat:
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Processing Batch {index + 1}...'):
                rok = datetime.now().year
                t0 = Task(description=f"Find {rok} news on: '{pojedynczy_temat}'.", expected_output="Facts/URLs.", agent=researcher)
                
                # ZADANIE ZE ŚCISŁĄ WERYFIKACJĄ KORPO-BEŁKOTU
                t1 = Task(
                    description=(
                        "Write a sharp, blunt LinkedIn post based on the research. "
                        "Talk like a skeptic who only cares about ROI and logic. "
                        "STRICT RULE: Do not use any metaphors about games, music, or sports. "
                        "Do not use 'Not just X, but Y'. "
                        "If it sounds like a motivational speech, rewrite it to be more like a technical post-mortem."
                    ),
                    expected_output="A conversational, sharp, and non-cringe LinkedIn post. Factual and direct.",
                    agent=copywriter
                )
             
                t2 = Task(description="Midjourney prompt for this post.", expected_output="Prompt string.", agent=art_director)
                
                crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                crew.kickoff()
                
                post_text = getattr(t1.output, 'raw_output', str(t1.output))
                visual_prompt = getattr(t2.output, 'raw_output', str(t2.output))
                
                save_to_history(pojedynczy_temat, f"{post_text}\n\nPrompt: {visual_prompt}")
                
                clean_post = post_text.replace('\n', '<br>')
                
                st.markdown(f'''
                    <div class="result-card" style="font-family: 'Plus Jakarta Sans', sans-serif;">
                        <div style="font-weight: 800; color: #A765FF; font-size: 14px; letter-spacing: 1px; margin-bottom: 15px;">BATCH {index + 1} READY</div>
                        <div style="color: #1A1A1A; font-size: 16px; margin-bottom: 25px; font-weight: 400; line-height: 1.6;">{clean_post}</div>
                        <div style="background: #F4F4F9; padding: 20px; border-radius: 12px; border-left: 4px solid #FF66B2;">
                            <strong style="color: #000; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">📸 Visual Prompt</strong><br>
                            <span style="color: #444; font-size: 14px; font-style: italic;">{visual_prompt}</span>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                with st.expander("🔍 Sources, please!"):
                    st.write(getattr(t0.output, 'raw_output', str(t0.output)))
