import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
from langchain_core.tools import tool
from duckduckgo_search import DDGS

# --- PAGE CONFIG ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide")

# --- CUSTOM CSS (Branding Kellton Europe) ---
st.markdown("""
    <style>
    .main {
        background-color: #0A081B;
    }
    .stTextArea textarea {
        background-color: #161235;
        color: white;
        border: 1px solid #452DA2;
    }
    .stButton>button {
        background: linear-gradient(45deg, #452DA2, #FC64FF);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
    }
    .stAlert {
        background-color: rgba(69, 45, 162, 0.2);
        border: 1px solid #49E1DD;
        color: white;
    }
    [data-testid="stSidebar"] {
        background-color: #060514;
        border-right: 1px solid #452DA2;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PIN LOGIC ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("⚡ Kellton AI Access")
        pin = st.text_input("Enter your access PIN:", type="password")
        if st.button("Enter"):
            # Tutaj ustaw swój własny PIN
            if pin == "4014": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect PIN. Please try again.")
        return False
    return True

if check_password():
    # --- LOAD KEYS ---
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except:
        pass

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

    # --- AGENTS BRAND VOICE ---
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
    
    scrape_tool = ScrapeWebsiteTool()

    # --- TOOLS ---
    @tool("DuckDuckGo Web Search")
    def search_tool(search_query: str) -> str:
        """Search the web for the latest information, news, and data on a given topic."""
        try:
            with DDGS() as ddgs:
                # Pobieramy 4 najlepsze wyniki z sieci
                results = list(ddgs.text(search_query, max_results=4))
                if results:
                    # Od razu formatujemy to tak, żeby Agent widział linki
                    return "\n\n".join([f"Link: {r.get('href', '')}\nSnippet: {r.get('body', '')}" for r in results])
                return "No results found."
        except Exception as e:
            return f"Search failed: {str(e)}"

    # --- NOWY AGENT: RESEARCHER ---
    researcher = Agent(
        role='Senior Market Researcher',
        goal='Search the web for the latest, most accurate data, insights, and news regarding the requested topic.',
        backstory='You are a sharp B2B tech researcher. You ignore fluff and marketing jargon. You find hard facts, statistics, and fresh industry trends. You summarize findings into actionable bullet points.',
        verbose=True,
        tools=[search_tool]
    )

    copywriter = Agent(
        role='Lead Content Strategist',
        goal='Write sharp LinkedIn posts that lead with a benefit. Focus on thought leadership and trust for B2B decision-makers. Use a confident, conversational tone.',
        backstory=kellton_brand_voice,
        verbose=True,
        tools=[scrape_tool]
    )

    art_director = Agent(
        role='Art Director',
        goal='Generate ONE Nano Banana prompt. Style: Deep dark (#0A081B), 3D icons, glassmorphism, neon accents.',
        backstory="You stick to the Kellton Europe KV. Use negative space.",
        verbose=True
    )

    # --- APP LAYOUT ---
    st.sidebar.title("📚 Your archive")
    hist_df = load_history()
    
    if not hist_df.empty:
        st.sidebar.dataframe(hist_df[['Date', 'Topic/Notes']].tail(5), use_container_width=True)
        csv = hist_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.sidebar.download_button("📥 Download the CSV", data=csv, file_name="kellton_plan.csv", mime="text/csv")
    else:
        st.sidebar.info("No saved posts yet. Generate something!")
    
    st.title("My little Junior SoMe Specialist 🌞")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("Input")
        temat = st.text_area("What are we writing about today?", height=200, placeholder="Paste your notes here...")
        btn = st.button("GET TO WORK, BRO", type="primary")

    with col2:
        st.subheader("Result")
        if btn and temat:
            # Rozdzielamy tekst z okienka na osobne linijki (odrzucamy puste)
            lista_tematow = [t.strip() for t in temat.split('---') if t.strip()]
            
            st.write(f"I'm working: {len(lista_tematow)} queued posts.")
            
            # Pętla - Agenci pracują nad każdym tematem zupełnie osobno
            for index, pojedynczy_temat in enumerate(lista_tematow):
                with st.spinner(f'Generuję post {index + 1} z {len(lista_tematow)}...'):
                    # Zadanie 1: Research (Z wymuszonymi źródłami)
                    t0 = Task(
                        description=f"Search the web for the latest insights, news, and data on this topic: '{pojedynczy_temat}'. Extract the 3 most important facts. YOU MUST INCLUDE the exact URLs/links of your sources at the bottom of your notes.",
                        expected_output="A bulleted list of facts, ending with a 'Sources:' list containing exact URLs.",
                        agent=researcher
                    )
                    
                    # Zadanie 2: Copywriting (Zmodyfikowane - bierze dane z t0)
                    t1 = Task(
                        description=f"Read the research notes provided by the previous task. Write a LinkedIn post about it. Do NOT invent data. Follow your brand voice.",
                        expected_output="LinkedIn post text.",
                        agent=copywriter
                    )
                    
                    # Zadanie 3: Grafika (Zostaje bez zmian)
                    t2 = Task(
                        description="Read the final LinkedIn post and generate ONE Midjourney prompt for it.",
                        expected_output="Midjourney prompt string.",
                        agent=art_director
                    )
                    
                    # Zmiana: Crew musi teraz uwzględniać 3 Agentów i 3 Zadania w odpowiedniej kolejności!
                    crew = Crew(agents=[researcher, copywriter, art_director], tasks=[t0, t1, t2])
                    
                    wynik = str(crew.kickoff())
                    save_to_history(pojedynczy_temat, wynik)
                    
                    st.success("Batch is ready!")
                    st.info(wynik)
                    
                    # NOWOŚĆ: Rozwijany panel ze źródłami
                    with st.expander("🔍 Sources, please!"):
                        surowe_notatki = getattr(t0.output, 'raw_output', str(t0.output))
                        st.write(surowe_notatki)
                                  
                    
        elif btn:
            st.warning("Please enter a topic first!")
