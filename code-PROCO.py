import streamlit as st
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# 1. App-Einrichtung
st.set_page_config(
    page_title="ProCo - KI Debatten-Plattform",
    page_icon="⚖️",
    layout="wide"
)

# Verlauf im Speicher initialisieren, falls er noch nicht existiert
if "verlauf" not in st.session_state:
    st.session_state.verlauf = []

# Hilfsfunktion für das Hintergrundbild
def get_background_url(query):
    if not query:
        return "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=1600"
    search_term = query.replace(" ", ",").replace("?", "")
    return f"https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=1600&auto=format&fit=crop&sig={search_term}"

# Aktuelles Thema ermitteln
current_input = st.session_state.get("user_input_key", "")
bg_url = get_background_url(current_input)

# Premium-Design mit starkem Kontrast für perfekte Lesbarkeit
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    .stApp {{
        background: url('{bg_url}') no-repeat center center fixed; 
        background-size: cover;
    }}
    
    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    
    /* Dunkler, edler Titel über dem Bild */
    .main-title {{ 
        font-size: 3.8rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.2rem; 
        letter-spacing: -1px;
    }}
    
    .subtitle {{ 
        font-size: 1.25rem; 
        text-align: center; 
        color: #0f172a; 
        font-weight: 700;
        margin-bottom: 3rem; 
        background-color: rgba(255, 255, 255, 0.7);
        padding: 5px 15px;
        border-radius: 10px;
        display: inline-block;
        margin-left: auto;
        margin-right: auto;
    }}
    
    /* Karten sind jetzt solid und dunkelgrau/anthrazit gefärbt für maximalen Schriftkontrast */
    .pro-card {{ 
        background-color: #1e293b; 
        color: #f8fafc !important;
        padding: 26px; 
        border-radius: 20px; 
        border-left: 6px solid #10b981;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px; 
    }}
    
    .con-card {{ 
        background-color: #1e293b; 
        color: #f8fafc !important;
        padding: 26px; 
        border-radius: 20px; 
        border-left: 6px solid #ef4444;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px; 
    }}
    
    .fazit-card {{ 
        background-color: #0f172a; 
        color: #f8fafc !important;
        padding: 30px; 
        border-radius: 20px; 
        border-top: 6px solid #6366f1; 
        box-shadow: 0 20px 40px -5px rgba(0, 0, 0, 0.4);
        margin-top: 30px; 
    }}
    
    /* Erzwingt weiße Textfarbe für Markdown-Listen in den Karten */
    .pro-card p, .pro-card li, .con-card p, .con-card li, .fazit-card p, .fazit-card li {{
        color: #f8fafc !important;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚖️ ProCo</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center;"><div class="subtitle">Zwei Perspektiven. Aktuelle Live-Fakten. Deine Meinungsbildung.</div></div>', unsafe_allow_html=True)

# --- SIDEBAR MIT EINSTELLUNGEN & VERLAUF ---
with st.sidebar:
    st.header("⚙️ Einstellungen")
    anzahl_argumente = st.slider(
        "Anzahl der Argumente pro Seite:",
        min_value=1,
        max_value=8,
        value=4
    )
    
    st.write("---")
    st.header("🕒 Letzte 10 Diskussionen")
    
    # Verlauf anzeigen. Wenn ein Button geklickt wird, wird das Suchfeld befüllt
    for eintrag in st.session_state.verlauf:
        if st.button(f"🔍 {eintrag}", key=f"hist_{eintrag}", use_container_width=True):
            st.session_state.user_input_key = eintrag
            st.rerun()

# Das große Eingabefeld
user_input = st.text_input(
    "Gib eine These oder Fragestellung ein:",
    placeholder="z. B. Sollte künstliche Intelligenz an Schulen erlaubt sein?",
    key="user_input_key"
)

# Thema zum Verlauf hinzufügen (Doppelte vermeiden, max. 10 Einträge)
if user_input and user_input not in st.session_state.verlauf:
    st.session_state.verlauf.insert(0, user_input)
    if len(st.session_state.verlauf) > 10:
        st.session_state.verlauf.pop()
    st.rerun()

def get_web_context(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=4)]
            return "\n\n".join(results)
    except Exception:
        return "Keine aktuellen Webdaten gefunden. Nutze internes Wissen."

if user_input:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Fehler: Kein Gemini API-Key gefunden!")
        st.stop()

    with st.spinner("Generiere Debatte..."):
        try:
            client = genai.Client(api_key=api_key)
            search_context = get_web_context(user_input)
            
            debatten_instruction = (
                "Du bist ein analytischer Debatten-Bot. Generiere starke Argumente basierend auf dem Kontext. "
                "Antworte auf Deutsch. Trenne die beiden Blöcke strikt mit dem Textzeichen '---TRENNUNG---'.\n\n"
                f"Format:\n### 🟢 Pro-Argumente\n[Hier genau {anzahl_argumente} Aufzählungspunkte]\n"
                "---TRENNUNG---\n"
                f"### 🔴 Kontra-Argumente\n[Hier genau {anzahl_argumente} Aufzählungspunkte]"
            )
            
            base_prompt = f"Thema: {user_input}\n\nAktueller Web-Kontext:\n{search_context}\n\n"

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=base_prompt,
                config=types.GenerateContentConfig(system_instruction=debatten_instruction)
            )

            ergebnis = response.text
            
            if "---TRENNUNG---" in ergebnis:
                pro_text, con_text = ergebnis.split("---TRENNUNG---")
            else:
                pro_text = ergebnis
                con_text = "### 🔴 Kontra-Argumente\n* Fehler beim automatischen Aufteilen der Argumente."

            # Spalten-Layout anzeigen
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="pro-card">', unsafe_allow_html=True)
                st.markdown(pro_text.strip())
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="con-card">', unsafe_allow_html=True)
                st.markdown(con_text.strip())
                st.markdown('</div>', unsafe_allow_html=True)

            # Neutrales Fazit
            st.markdown('<div class="fazit-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color: #6366f1;">🤖 Impuls zur Meinungsbildung</h3>', unsafe_allow_html=True)
            
            fazit_prompt = (
                f"Fasse diese Debatte zu '{user_input}' in einem kurzen, absolut neutralen Fazit zusammen. "
                f"Zeige sachlich auf, worauf es ankommt.\n\nPro:\n{pro_text}\n\nKontra:\n{con_text}"
            )

            fazit_response = client.models.generate_content(model='gemini-2.5-flash', contents=fazit_prompt)
            st.markdown(fazit_response.text)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")
