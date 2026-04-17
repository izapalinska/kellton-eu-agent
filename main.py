import os
import streamlit as st
import pandas as pd
from datetime import datetime
from crewai import Agent, Task, Crew

# --- Wczytanie kluczy z pliku .env ---
try:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
except FileNotFoundError:
    st.error("Błąd: Nie znaleziono pliku .env.")

# --- Funkcje obsługi historii ---
FILE_NAME = "historia_postow.csv"

def zapisz_do_historii(temat, tresc_posta):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nowa_linia = pd.DataFrame([[now, temat, tresc_posta]], columns=['Data', 'Notatka', 'Wygenerowana Treść'])
    
    if not os.path.isfile(FILE_NAME):
        nowa_linia.to_csv(FILE_NAME, index=False, encoding='utf-8-sig')
    else:
        nowa_linia.to_csv(FILE_NAME, mode='a', header=False, index=False, encoding='utf-8-sig')

def wczytaj_historie():
    if os.path.isfile(FILE_NAME):
        return pd.read_csv(FILE_NAME, encoding='utf-8-sig')
    return pd.DataFrame(columns=['Data', 'Notatka', 'Wygenerowana Treść'])

# --- Konfiguracja Agentów (Brand Voice & Agenci) ---
# (Zostawiamy Twoje sprawdzone ustawienia bez zmian)
kellton_brand_voice = """
Identity & Purpose:
* Who we are: Kellton Europe, a trusted digital transformation partner.
* Our Message: "The results you need. The partnership you want."
* Audience: Senior leaders (CTO, CIO, CEO) who hate fluff and buzzwords.
The "No Bullshit" Writing Style:
* Be Casual: Use contractions. If it sounds stiff, rewrite it.
* Be Confident: Use strong, declarative sentences. Take a clear stance.
* Active Voice Only: Say "We build apps," not "Apps are built by us".
* Lead with Benefits: Start with what the reader gets.
* Conversational Punctuation: Use a spaced en-dash ( – ) for pauses.
Strict Negative Constraints:
* NEVER use: Synergy, leverage, paradigm shift, game-changing, revolutionary, utilize, actionable insights, low-hanging fruit, circle back, touch base.
* No Em-dashes (—): Use the spaced en-dash ( – ) instead.
"""

copywriter = Agent(
    role='Lead Content Strategist & Copywriter',
    goal='Break down complex technical inputs into engaging LinkedIn posts.',
    backstory=kellton_brand_voice,
    verbose=True,
    allow_delegation=False
)

art_director = Agent(
    role='Senior Art Director',
    goal='Tworzenie jednego, idealnego promptu do Midjourney w stylu Kellton Europe.',
    backstory="""Jesteś dyrektorem artystycznym Kellton Europe. Styl: Deep dark background (#0A081B), 
    minimalist 3D icons, glassmorphism, neon purple/pink/cyan accents. Dużo negative space. 
    Wygeneruj JEDEN techniczny prompt zaczynający się od '🎨 VISUAL PROMPT: /imagine prompt:'.""",
    verbose=True,
    allow_delegation=False
)

# --- INTERFEJS STREAMLIT ---
st.set_page_config(page_title="Kellton Content Engine", page_icon="⚡", layout="wide")

# Pasek boczny z historią
st.sidebar.title("📚 Historia i Eksport")
historia_df = wczytaj_historie()

if not historia_df.empty:
    st.sidebar.write("Ostatnie posty:")
    # Pokazujemy tylko datę i notatkę w podglądzie
    st.sidebar.dataframe(historia_df[['Data', 'Notatka']].tail(10), use_container_width=True)
    
    # Przycisk do pobrania pliku CSV pod Planable
    csv = historia_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
    st.sidebar.download_button(
        label="📥 Pobierz CSV dla Planable",
        data=csv,
        file_name=f"kellton_social_plan_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
    
    if st.sidebar.button("🗑️ Wyczyść historię"):
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            st.rerun()
else:
    st.sidebar.info("Brak zapisanych postów. Wygeneruj coś!")

# Główny panel
st.title("⚡ Kellton Content Generator")
temat_input = st.text_area("O czym piszemy dzisiaj?", height=120, placeholder="Twoje notatki lub pomysł...")

if st.button("🚀 Generuj Pakiet Contentowy", type="primary"):
    if temat_input.strip():
        with st.spinner('Twoi Agenci tworzą content...'):
            task_copy = Task(
                description=f"Napisz krótki post na LinkedIn (maks 5 zdań) o: '{temat_input}'. Zakończ pytaniem i dodaj 2 hashtagi.",
                expected_output='Post na LinkedIn po angielsku.',
                agent=copywriter
            )
            task_design = Task(
                description="Dodaj do posta prompt wizualny do Midjourney na samym dole.",
                expected_output='Oryginalny post + prompt wizualny.',
                agent=art_director
            )
            
            crew = Crew(agents=[copywriter, art_director], tasks=[task_copy, task_design])
            wynik = str(crew.kickoff())
            
            # ZAPIS DO HISTORII
            zapisz_do_historii(temat_input, wynik)
            
            st.success("Gotowe! Post został zapisany w historii.")
            st.markdown("### Wynik pracy zespołu:")
            st.info(wynik)
            
            # Przycisk do odświeżenia paska bocznego
            st.button("Odśwież historię w panelu")
    else:
        st.warning("Pole nie może być puste.")