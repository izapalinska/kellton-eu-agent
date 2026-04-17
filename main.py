import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew

# --- KONFIGURACJA STRONY ---
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

# --- LOGIKA PINU ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("⚡ Kellton AI Access")
        pin = st.text_input("Wpisz swój PIN dostępu:", type="password")
        if st.button("Wejdź"):
            # Tutaj ustaw swój własny PIN
            if pin == "1234": 
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Zły PIN. Spróbuj jeszcze raz.")
        return False
    return True

if check_password():
    # --- WCZYTANIE KLUCZY ---
    # W chmurze używamy st.secrets zamiast .env
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except:
        pass

    # --- HISTORIA ---
    FILE_NAME = "historia_postow.csv"
    def zapisz_do_historii(temat, tresc_posta):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df = pd.DataFrame([[now, temat, tresc_posta]], columns=['Data', 'Notatka', 'Wygenerowana Treść'])
        if not os.path.isfile(FILE_NAME):
            df.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')

    def wczytaj_historie():
        if os.path.isfile(FILE_NAME):
            return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
        return pd.DataFrame(columns=['Data', 'Notatka', 'Wygenerowana Treść'])

    # --- AGENCI ---
    kellton_brand_voice = """
    Identity: Kellton Europe. Results-oriented, "No Bullshit", casual but sharp. 
    Style: Active voice, use contractions, no fluff.
    Banned: synergy, leverage, game-changing, revolutionary, utilize, delve, etc.
    Constraint: No "Not just X, but Y". Use spaced en-dash ( – ).
    """

    copywriter = Agent(
        role='Lead Content Strategist',
        goal='Write sharp LinkedIn posts (max 5 sentences) that lead with a benefit.',
        backstory=kellton_brand_voice,
        verbose=True
    )

    art_director = Agent(
        role='Art Director',
        goal='Generate ONE Midjourney prompt. Style: Deep dark (#0A081B), 3D icons, glassmorphism, neon accents.',
        backstory="You stick to the Kellton Europe KV. Use negative space.",
        verbose=True
    )

    # --- LAYOUT APKI ---
    st.sidebar.title("📚 Twoje Archiwum")
    hist_df = wczytaj_historie()
    
    if not hist_df.empty:
        st.sidebar.dataframe(hist_df[['Data', 'Notatka']].tail(5), use_container_width=True)
        csv = hist_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.sidebar.download_button("📥 Pobierz dla Planable", data=csv, file_name="kellton_plan.csv", mime="text/csv")
    
    st.title("⚡ Kellton Content Engine")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader("Wejście")
        temat = st.text_area("O czym dziś piszemy?", height=200, placeholder="Wklej notatki...")
        btn = st.button("🚀 GENERUJ CONTENT", type="primary")

    with col2:
        st.subheader("Wynik")
        if btn and temat:
            with st.spinner('Agenci pracują...'):
                t1 = Task(description=f"Write post about: {temat}", expected_output="LinkedIn post", agent=copywriter)
                t2 = Task(description="Add MJ prompt at the end.", expected_output="Post + Prompt", agent=art_director)
                crew = Crew(agents=[copywriter, art_director], tasks=[t1, t2])
                wynik = str(crew.kickoff())
                zapisz_do_historii(temat, wynik)
                st.info(wynik)
        elif btn:
            st.warning("Najpierw coś wpisz!")
