import os
import random
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import requests
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

def send_external_notification(topic):
    # Wymyśl bardzo nietypową nazwę kanału (np. z ciągiem cyfr, żeby nikt tu nie wszedł)
    url = "https://ntfy.sh/kellton_content_alerts_8833" 
    
    wiadomosc = f"Post: {topic} is ready!"
    
    try:
        # Wysyłamy sygnał push
        requests.post(url, data=wiadomosc.encode('utf-8'), headers={
            "Title": "Kellton Content Engine",
            "Tags": "white_check_mark"
        })
    except:
        pass

def generate_quote_card(main_header, sub_header):
    bg_folder = "backgrounds"
    try:
        bg_files = [f for f in os.listdir(bg_folder) if f.endswith(('.png', '.jpg'))]
        if not bg_files:
            raise FileNotFoundError("Folder is empty!")
        random_bg = random.choice(bg_files)
        bg_path = os.path.join(bg_folder, random_bg)
        img = Image.open(bg_path)
    except (FileNotFoundError, OSError):
        # Format 1080x1350 (pion)
        img = Image.new('RGB', (1080, 1350), color=(15, 15, 18))
    
    draw = ImageDraw.Draw(img)
    
    try:
        # Ładujemy dwa rozmiary tego samego fontu
        font_large = ImageFont.truetype("Figtree-Medium.ttf", 120) # Główny, duży tytuł
        font_small = ImageFont.truetype("Figtree-Medium.ttf", 45) # Mniejszy podtytuł
    except IOError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    x_text = 65
    y_text = 320 # Punkt startowy od góry
    
    # 1. Rysujemy DUŻY NAGŁÓWEK
    lines_main = textwrap.wrap(main_header, width=18) 
    for line in lines_main:
        draw.text((x_text, y_text), line, font=font_large, fill=(255, 255, 255))
        y_text += 130 # Duży odstęp dla kolejnej linijki wielkiego tekstu
        
    y_text += 80 # Dodatkowy, pusty odstęp między nagłówkami
    
    # 2. Rysujemy MAŁY NAGŁÓWEK (Rozwinięcie)
    # Większa szerokość wrapowania, bo font jest mniejszy
    lines_sub = textwrap.wrap(sub_header, width=35)
    for line in lines_sub:
        # Możemy dać mu lekko szarawy odcień RGB(200,200,200), żeby duży tekst bardziej krzyczał, 
        # albo zostawić czystą biel (255,255,255)
        draw.text((x_text, y_text), line, font=font_small, fill=(220, 220, 220))
        y_text += 60 # Mniejszy odstęp dla mniejszego tekstu
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
    
    
# --- 3. CUSTOM CSS (FULL REPAIRED VERSION) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Instrument+Serif:ital@0;1&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #030303;
    }

    /* TYTUŁY */
    .main-title {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 82px !important;
        font-weight: 800;
        margin-bottom: 20px !important;
        letter-spacing: -4px;
        line-height: 1;
        background: linear-gradient(90deg, #FFFFFF, #A765FF, #FF66B2, #FFFFFF);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 5s linear infinite;
    }
    @keyframes shine { to { background-position: 200% center; } }

    .serif-akcent {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 52px !important;
        letter-spacing: 4px !important;
        color: #FF66B2; 
        display: block;
        margin-top: -35px !important;
        margin-bottom: 4rem;
    }

    /* SIDEBAR - SZKLANY EFEKT */
    [data-testid="stSidebar"] {
        background: rgba(6, 5, 20, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* NAPRAWA STRZAŁKI SIDEBARU (UKRYWAMY TYLKO TŁO HEADEREM, NIE CAŁY HEADER) */
    header {
        background-color: transparent !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* PRZYCISK "GET TO WORK" - KOLORY I GLOW */
    div[data-testid="stButton"] > button {
        background: linear-gradient(90deg, #E31352 0%, #F86652 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 18px 30px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        width: 100%;
        box-shadow: 0 4px 15px rgba(227, 19, 82, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 0 20px rgba(227, 19, 82, 0.6), 0 0 40px rgba(248, 102, 82, 0.2) !important;
        color: white !important;
    }

    /* KARTA WYNIKÓW */
    .result-card {
        background: #0F0F12 !important;
        color: #EDEDED !important;
        padding: 30px;
        border-radius: 24px;
        margin-bottom: 30px;
        border: 1px solid rgba(167, 101, 255, 0.2);
        box-shadow: 0 15px 45px rgba(0,0,0,0.7);
    }

    /* IKONY NAGŁÓWKÓW */
    .header-with-icon {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }

    /* INPUTY I TABELE */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        border-radius: 15px;
        overflow: hidden;
        border: 1px solid rgba(167, 101, 255, 0.1);
    }
    div[data-baseweb="textarea"] > div, div[data-baseweb="input"] > div {
        background-color: #0F0F11 !important;
        border: 1px solid #2A1F5C !important;
        border-radius: 16px !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    
    <svg width="0" height="0" style="position:absolute">
      <defs>
        <linearGradient id="icon-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#A765FF" />
          <stop offset="100%" style="stop-color:#FF66B2" />
        </linearGradient>
      </defs>
    </svg>
    """, unsafe_allow_html=True)

# --- 4. PIN LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('''
        <div class="header-with-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="url(#icon-grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            <h1 class="main-title" style="font-size: 50px !important; margin-bottom: 0px !important;">Security Check</h1>
        </div>
        <p style="color: #666; margin-bottom: 25px;">Czołem, kluski z rosołem!</p>
    ''', unsafe_allow_html=True)
    
    pin = st.text_input("Enter Access PIN:", type="password")
    if st.button("UNLOCK ACCESS"):
        if pin == "4014": 
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Access Denied.")
    st.stop()

# --- 5. LOAD KEYS & TOOLS ---
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]
os.environ["OPENAI_MODEL_NAME"] = "gpt-5-mini"

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
You are the Smart Insider at Kellton Europe, writing insightful LinkedIn posts for the company profile. 
You are confident, casual, and highly competent.

CRITICAL RULE: You are generating the FINAL post to be published. DO NOT talk to the prompter. DO NOT reference the research you did (e.g., never say "reports I reviewed"). DO NOT offer follow-up information. Output ONLY the post content.

STRICT RULE: ALWAYS WRITE THE FINAL OUTPUT IN ENGLISH. Even if the conversation context is different.

TARGET AUDIENCE:
Pragmatic, results-oriented senior leaders (CTO, CIO, CEO) who hate fluff and buzzwords.

TONE & STYLE:
- Confident LinkedIn creator: Be natural, approachable, and witty, but professional. (Use "We" for Kellton).
- Start with a hook: Ask a provocative question, drop a stat, or start mid-thought.
- Natural rhythm: Use contractions (it’s, don’t). Use a spaced en-dash ( – ) for pauses.
- The Pub Test: If it sounds like a PowerPoint slide, delete it. If it sounds like a smart observation at a bar, keep it.
- Emojis: Use 1-2 max, only to format lists or add a subtle touch. No winking faces (😉).

THE ANTI-PROFESSOR RULE (CRITICAL):
- NEVER provide dictionary definitions of tech terms (e.g., "AI is...", "ML is a subset..."). Assume the CTO reader already knows what they are.
- Turn technical features into business consequences.

STRUCTURE (THE 2-1-3 RULE):
Follow this exact formatting for breathability:
1. OPENING (1-2 sentences): The Hook.
2. THE MEAT (1 sentence OR a clean bulleted list): If using a list, make it 3-4 short points with line breaks. NEVER use a dense, comma-separated block of text.
3. THE TAKEAWAY (1-3 sentences max): The conclusion or advice.

STRICT NEGATIVE CONSTRAINTS (HARD BAN):
1. NO AI-ASSISTANT TALK: Never offer to send more info. Never say "Here is the post."
2. NO HYPE: Ban "VIP", "jazz", "chess", "checkers", "playbook", "underdogs", "strings", "sauce", "recipe", "flashy", "growth lever", "tangible", "strategic", "no buzz, no fluff".
3. NO CORPORATE BUZZWORDS: synergy, leverage, game-changing, revolutionary, robust, seamless, cutting-edge, secret sauce, heavy lifting.
4. NO BINARY CONTRAST: Never use "Not just X, but Y". 
5. NO "In 2026...". Start with the problem.
6. NO DRAMA: Ban "financial suicide", "adapt or be left behind", "winners", "shift is clear".
7. NO SALES PITCHES: Never sound like a brochure when mentioning Kellton.

THE CHARISMA TEST:
If it sounds like an automated bank email OR a chatbot offering help, delete it. 
If it sounds like a sharp observation from a respected colleague - keep it.

EXAMPLES OF THE REAL KELLTON STYLE:
[BAD - Hype]: "Outsourcing is like a jazz quartet – smooth and innovative."
[GOOD - Blunt]: "Most outsourcing fails because the incentives are wrong. In 2026, if you're still paying for hours instead of outcomes, you're literally funding your vendor's inefficiency."

[BAD - Cliché]: "Stop playing checkers and start playing chess with your strategy."
[GOOD - Blunt]: "Hiring an AI team is a headcount move. The real strategy is knowing which parts of your legacy stack will actually survive the migration."

[BAD]: "Companies are waking up to the fact that AI is essential for the landscape."
[GOOD]: "AI for the sake of AI is a waste of money. Most projects fail because the architecture is weak, not because the model isn't 'smart' enough."

[BAD - Academic Definition]: "Machine Learning is a subset of AI that uses data to learn patterns and make predictions without being explicitly programmed."
[GOOD - Business Consequence]: "Half the companies shopping for 'AI' right now actually just need a well-written SQL query. Stop asking vendors if they use AI. Ask them to prove their model works on your messy data – and tie their invoice to the accuracy rate."
"""


researcher = Agent(
    role='Senior Market Researcher',
    goal='Search for 2026 data and trends or extract content from specific URLs.',
    backstory='Sharp B2B researcher. Translates topics into English queries and extracts key insights from websites.',
    verbose=True,
    tools=[search_tool, scrape_tool] # scrape_tool TUTAJ
)

copywriter = Agent(
    role='Lead Content Strategist',
    goal='Write sharp LinkedIn posts based strictly on research.',
    backstory=kellton_brand_voice,
    verbose=True,
    tools=[scrape_tool]
)

editor = Agent(
    role='Ruthless Chief Editor',
    goal='Ensure the post strictly adheres to the Kellton Europe brand voice and eliminate all AI fluff and corporate jargon.',
    backstory=(
        "You are the brutal, no-nonsense editor at Kellton Europe. "
        "Your job is to read the copywriter's draft and ruthlessly edit it. "
        "You HATE words like: synergy, leverage, paradigm shift, game-changing, disrupt, revolutionary, utilize, actionable insights, low-hanging fruit, circle back, robust, seamless, state-of-the-art. "
        "You ensure the tone is confident, casual, and sharp. You write like you talk, using contractions (it's, you're, we'll). "
        "If it sounds like an academic paper, a sales brochure, or typical AI-generated fluff, you rewrite it. "
        "You demand active voice."
    ),
    verbose=True
)

art_director = Agent(
    role='Art Director',
    goal='Generate ONE Midjourney prompt.',
    backstory="Kellton Europe KV style. Use negative space.",
    verbose=True
)

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('''
        <div class="header-with-icon" style="margin-top: 20px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="url(#icon-grad)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"></polyline><rect x="1" y="3" width="22" height="5"></rect><line x1="10" y1="12" x2="14" y2="12"></line></svg>
            <span style="font-weight: 700; color: #A765FF; font-size: 18px;">Archives</span>
        </div>
    ''', unsafe_allow_html=True)
    
    hist_df = load_history()
    if not hist_df.empty:
        st.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
    
    st.download_button(label="EXPORT CSV", data=hist_df.to_csv(index=False).encode('utf-8-sig'), file_name="kellton_data.csv", mime="text/csv", use_container_width=True)

# --- 8. WIDOK GŁÓWNY ---
st.markdown('<h1 class="main-title">KELLTON EUROPE</h1>', unsafe_allow_html=True)
st.markdown('<span class="serif-akcent">Social Media Specialist</span>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.4], gap="large")

with col1:
    st.markdown('''
        <div class="header-with-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#icon-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            <span style="font-weight: 700; font-size: 24px; color: #A765FF;">WHAT ARE WE WRITING ABOUT?</span>
        </div>
    ''', unsafe_allow_html=True)
    temat = st.text_area("", height=250, placeholder="Use any input language you want and separate each idea with ---", label_visibility="collapsed")
    
    # DODANY TOGGLE:
    use_research = st.toggle("🔍 Enable web research", value=True, help="Turn off to generate a post strictly from your input without searching the web.")

    source_url = st.text_input("Source URL (Optional)", placeholder="Paste a link to a blog post, news, or report...")
   
    # DODANY WYBÓR FORMATU:
    post_format = st.selectbox(
        "Select post format",
        options=["Standard post", "Carousel outline", "LinkedIn poll", "Case study"],
        index=0
    )
    
    btn = st.button("GET TO WORK, BRO")


with col2:
    st.markdown('''
        <div class="header-with-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#icon-grad)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            <span style="font-weight: 700; font-size: 24px; color: #A765FF;">RESULT</span>
        </div>
    ''', unsafe_allow_html=True)

    # --- 1. INICJALIZACJA PAMIĘCI ---
    if 'wygenerowane_posty' not in st.session_state:
        st.session_state.wygenerowane_posty = []

    # --- 2. FAZA GENEROWANIA (Pracuje tylko po kliknięciu "GET TO WORK") ---
    if btn and temat:
        st.session_state.wygenerowane_posty = [] # Czyścimy starą pamięć
        lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
        
        for index, pojedynczy_temat in enumerate(lista_tematow):
            with st.spinner(f'Processing Batch {index + 1}...'):
                
                format_rules = ""
                if post_format == "Carousel outline":
                    format_rules = "OVERRIDE STRUCTURE: Do NOT use the 2-1-3 rule. Write this strictly as a LinkedIn Carousel outline (Slide 1, Slide 2, etc.)."
                elif post_format == "LinkedIn poll":
                    format_rules = "OVERRIDE STRUCTURE: Do NOT use the 2-1-3 rule. Write this strictly as a LinkedIn Poll (Question -> Context -> Options)."
                elif post_format == "Case study":
                    format_rules = "OVERRIDE STRUCTURE: Do NOT use the 2-1-3 rule. Use a Case Study structure (Problem, Fix, Result)."
                else:
                    format_rules = "STRUCTURE RULE: Strictly follow the 2-1-3 structure (Hook, Meat, Takeaway) as defined in your identity."

                tasks_list = []
                agents_list = []

                if use_research:
                    if source_url:
                        research_prompt = f"Scrape and analyze the content from this URL: {source_url}. Focus on how it relates to: '{pojedynczy_temat}'."
                    else:
                        research_prompt = f"Find 2026 news on: '{pojedynczy_temat}'."

                    t0 = Task(
                        description=(
                            f"{research_prompt} "
                            "STRICT RULE: Return a numbered list of key facts and insights. "
                            "CRITICAL: You MUST include the source URL for every fact or insight you provide. "
                            "No conversational filler. Start immediately with point 1."
                        ),
                        expected_output="A numbered list of facts, each followed by its source URL.",
                        agent=researcher
                    )
                    tasks_list.append(t0)
                    agents_list.append(researcher)
                    
                    t1_desc = (
                        f"Write a charismatic LinkedIn post based on the research provided. "
                        f"{format_rules} "
                        "STRICT RULES: No metaphors. No 'Not just X, but Y'. "
                        "LANGUAGE RULE: Write in English. Keep it under 150 words."
                    )
                else:
                    t1_desc = (
                        f"Write a charismatic LinkedIn post based EXACTLY on this input: '{pojedynczy_temat}'. "
                        "Do not search for external facts. "
                        f"{format_rules} "
                        "STRICT RULES: No metaphors. No 'Not just X, but Y'. "
                        "LANGUAGE RULE: Write in English. Keep it under 150 words."
                    )

                t1 = Task(description=t1_desc, expected_output="A charismatic LinkedIn content.", agent=copywriter)
                tasks_list.append(t1)
                agents_list.append(copywriter)

                t_edit = Task(
                    description=(
                        "Review the draft. "
                        "1. Kill all jargon. "
                        "2. Ensure contractions are used. "
                        "LANGUAGE RULE: Write in English. Keep it under 150 words."
                        "STRICT RULES: No metaphors. No 'Not just X, but Y'. "
                        "Ensure the tone is casual, yet informative."
                        f"3. CRITICAL: Maintain the requested {post_format} structure. If it is a Poll, do not turn it into a standard post."
                    ),
                    expected_output="Final polished content.",
                    agent=editor
                )
                tasks_list.append(t_edit)
                agents_list.append(editor)

                if post_format != "LinkedIn poll":
                    t2 = Task(description="Nano Banana prompt for this post.", expected_output="Prompt string.", agent=art_director)
                    tasks_list.append(t2)
                    agents_list.append(art_director)
                
                crew = Crew(agents=agents_list, tasks=tasks_list)
                crew.kickoff()
                
                # Zbieranie wyników po cichu
                post_text = getattr(t_edit.output, 'raw_output', str(t_edit.output))
                
                if post_format != "LinkedIn poll":
                    visual_prompt = getattr(t2.output, 'raw_output', str(t2.output))
                else:
                    visual_prompt = "N/A - Polls do not require images."
                
                if use_research:
                    research_out = getattr(t0.output, 'raw_output', str(t0.output))
                else:
                    research_out = "Web research was disabled for this post."
                
                save_to_history(pojedynczy_temat, f"{post_text}\n\nPrompt: {visual_prompt}")
                send_external_notification(pojedynczy_temat)
                
                # ZAPIS DO PAMIĘCI STREAMLITA (Kluczowy krok)
                st.session_state.wygenerowane_posty.append({
                    "post_text": post_text,
                    "visual_prompt": visual_prompt,
                    "research_out": research_out,
                    "format": post_format
                })

    if st.session_state.wygenerowane_posty:
        for index, dane in enumerate(st.session_state.wygenerowane_posty):
            
            html_code = f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
                * {{ font-family: 'Plus Jakarta Sans', sans-serif; }}
            </style>
            <div style="background: transparent; padding: 5px;">
                <div style="background: #0F0F12; color: #EDEDED; padding: 30px; border-radius: 24px; border: 1px solid rgba(167, 101, 255, 0.2); box-shadow: 0 15px 45px rgba(0,0,0,0.7);">
                    
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <span style="font-weight: 800; color: #A765FF; font-size: 14px; letter-spacing: 0.5px;">BATCH {index + 1}</span>
                        <button id="btn-post-{index}" onclick="copyToClipboard('post-text-{index}', 'btn-post-{index}')" style="background: #A765FF; color: white; border: none; border-radius: 8px; padding: 8px 16px; cursor: pointer; font-size: 11px; font-weight: 800; transition: 0.3s; text-transform: uppercase; box-shadow: 0 4px 10px rgba(167, 101, 255, 0.3);">COPY</button>
                    </div>
                    
                    <div id="post-text-{index}" style="line-height: 1.6; font-size: 15px; margin-bottom: 30px; font-weight: 400;">
                        {dane['post_text'].replace(chr(10), '<br>')}
                    </div>

                    <div style="padding: 20px; background: rgba(255,255,255,0.03); border-radius: 16px; border-left: 3px solid #FF66B2;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <small style="color: #FF66B2; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;">VISUAL DESIGN PROMPT</small>
                            <button id="btn-prompt-{index}" onclick="copyToClipboard('prompt-text-{index}', 'btn-prompt-{index}')" style="background: #FF66B2; color: white; border: none; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 10px; font-weight: 800; transition: 0.3s; text-transform: uppercase; box-shadow: 0 4px 10px rgba(255, 102, 178, 0.3);">COPY</button>
                        </div>
                        <div id="prompt-text-{index}" style="font-style: italic; font-size: 14px; color: rgba(255,255,255,0.7); line-height: 1.5;">
                            {dane['visual_prompt']}
                        </div>
                    </div>
                </div>

                <script>
                    function copyToClipboard(elementId, buttonId) {{
                        var htmlContent = document.getElementById(elementId).innerHTML;
                        var copyText = htmlContent.replace(/<br\\s*\\/?>/gi, "\\n").replace(/<[^>]*>?/gm, '');
                        
                        var btn = document.getElementById(buttonId);
                        var originalText = btn.innerText;
                        btn.innerText = "COPIED!";
                        btn.style.opacity = "0.8";
                        setTimeout(function() {{
                            btn.innerText = originalText;
                            btn.style.opacity = "1";
                        }}, 2000);

                        var textArea = document.createElement("textarea");
                        textArea.value = copyText.trim();
                        textArea.style.position = "fixed";
                        textArea.style.left = "-9999px";
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{ document.execCommand('copy'); }} catch (err) {{ console.error('ERROR', err); }}
                        document.body.removeChild(textArea);
                    }}
                </script>
            </div>
            """
            components.html(html_code, height=550, scrolling=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- MODUŁ DO GRAFIK ---
            if dane['format'] in ["Standard post", "Case study"]:
                with st.expander("🎨 Generate simple graphic"):
                    header_input = st.text_area("Duży nagłówek (Główny przekaz)", value="Twoje hasło...", height=80, key=f"head_{index}")
                    sub_header_input = st.text_area("Mały tekst (Rozwinięcie)", value="Krótkie wyjaśnienie, które pojawi się niżej.", height=80, key=f"sub_{index}")
                    
                    if st.button("Wygeneruj PNG", key=f"btn_img_{index}"):
                        gotowa_grafika = generate_quote_card(header_input, sub_header_input)
                        st.image(gotowa_grafika, caption="Twój nowy post", use_container_width=True)
                        st.download_button(
                            label="⬇️ DOWNLOAD PNG",
                            data=gotowa_grafika,
                            file_name=f"kellton_post_{index}.png",
                            mime="image/png",
                            use_container_width=True
                        )
            
            # --- ŹRÓDŁA (TERAZ BEZPIECZNIE CZYTAJĄCE Z PAMIĘCI) ---
            with st.expander("🔍 Sources, please!"):
                # Tu czytamy z 'dane', a nie z 't0'!
                st.write(dane['research_out'])


