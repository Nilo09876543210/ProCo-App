import streamlit as st
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# 1. App-Einrichtung & Webseiten-Design
st.set_page_config(
    page_title="ProCo - KI Debatten-Plattform",
    page_icon="⚖️",
    layout="wide"
)

# Premium-Design mit modernem Hintergrund-Verlauf und Clean-Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
    
    /* Hintergrund der gesamten App */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main-title { 
        font-size: 3.8rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.2rem; 
        letter-spacing: -1px;
    }
    
    .subtitle { 
        font-size: 1.25rem; 
        text-align: center; 
        color: #64748b; 
        margin-bottom: 3rem; 
    }
    
    /* Modernisierte Karten mit sanftem Schatten */
    .pro-card { 
        background-color: #ffffff; 
        padding: 26px; 
        border-radius: 20px; 
        border-left: 6px solid #10b981;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px; 
    }
    
    .con-card { 
        background-color: #ffffff; 
        padding: 26px; 
        border-radius: 20px; 
        border-left: 6px solid #ef4444;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px; 
    }
    
    .fazit-card { 
        background-color: #ffffff; 
        padding: 30px; 
        border-radius: 20px; 
        border-top: 6px solid #6366f1; 
        box-shadow: 0 20px 40px -5px rgba(0, 0, 0, 0.07);
        margin-top: 30px; 
    }
    
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Titel und Subtitel
st.markdown('<div class="main-title">⚖️ ProCo</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Zwei Perspektiven. Aktuelle Live-Fakten. Sichere Meinungsbildung.</div>', unsafe_allow_html=True)

# Sidebar für die Einstellungen
with st.sidebar:
    st.header("⚙️ Einstellungen")
    anzahl_argumente = st.slider(
        "Anzahl der Argumente pro Seite:",
        min_value=1,
        max_value=8,
        value=4
    )
    st.write("---")
    st.caption("ProCo filtert unpassende Inhalte automatisch heraus.")

# Das große Eingabefeld
user_input = st.text_input(
    "Gib eine These oder Fragestellung ein:",
    placeholder="z. B. Sollte künstliche Intelligenz an Schulen erlaubt sein?",
)

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
        st.error("Fehler: Kein Gemini API-Key in den Streamlit Secrets gefunden!")
        st.stop()

    with st.spinner("Prüfe Inhalt und generiere Debatte..."):
        try:
            client = genai.Client(api_key=api_key)
            
            # --- NEU: SICHERHEITS- UND INHALTS-CHECK ---
            check_instruction = (
                "Du bist ein Sicherheits-Filter. Analysiere das folgende Thema. "
                "Wenn das Thema illegale Aktivitäten, Hassrede, Gewalt, explizite Inhalte "
                "oder völlig unpassenden/unsinnigen Content enthält, antworte AUSSCHLIESSLICH mit dem Wort 'BLOCK'. "
                "Wenn das Thema sicher und eine normale Debattenfrage ist, antworte AUSSCHLIESSLICH mit 'OK'."
            )
            
            check_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Thema: {user_input}",
                config=types.GenerateContentConfig(system_instruction=check_instruction)
            )
            
            # Falls die KI den Inhalt blockiert:
            if "BLOCK" in check_response.text.upper():
                st.warning("⚠️ **Hinweis zu den Inhalten:** Diese Fragestellung enthält unpassende, sensible oder nicht debattierfähige Inhalte. Bitte gib eine sachliche, gesellschaftliche oder wissenschaftliche These ein.")
                st.stop()
            
            # Wenn alles OK ist, geht es normal weiter:
            search_context = get_web_context(user_input)
            base_prompt = f"Thema: {user_input}\n\nAktueller Web-Kontext:\n{search_context}\n\n"

            # Anweisungen für die Bots (mit strikter Vorgabe für Formatierung)
            pro_instruction = (
                f"Du bist ein analytischer Debatten-Bot, der AUSSCHLIESSLICH starke Pro-Argumente liefert. "
                f"Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch. "
                f"Liefere als Überschrift '### 🟢 Pro-Argumente'. Liefere darunter EXAKT {anzahl_argumente} "
                f"übersichtliche Bulletpoints."
            )

            con_instruction = (
                f"Du bist ein analytischer Debatten-Bot, der AUSSCHLIESSLICH starke Kontra-Argumente liefert. "
                f"Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch. "
                f"Liefere als Überschrift '### 🔴 Kontra-Argumente'. Liefere darunter EXAKT {anzahl_argumente} "
                f"übersichtliche Bulletpoints."
            )

            # KI-Abfragen
            pro_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=base_prompt,
                config=types.GenerateContentConfig(system_instruction=pro_instruction)
            )

            con_response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=base_prompt,
                config=types.GenerateContentConfig(system_instruction=con_instruction)
            )

            # Spalten-Layout anzeigen
            col1, col2 = st.columns(2)

            with col1:
                st.markdown('<div class="pro-card">', unsafe_allow_html=True)
                st.markdown(pro_response.text)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="con-card">', unsafe_allow_html=True)
                st.markdown(con_response.text)
                st.markdown('</div>', unsafe_allow_html=True)

            # Neutrales Fazit
            st.markdown('<div class="fazit-card">', unsafe_allow_html=True)
            st.markdown('### 🤖 Impuls zur Meinungsbildung')
            
            fazit_prompt = (
                f"Fasse diese Debatte zu '{user_input}' in einem kurzen, absolut neutralen Fazit zusammen. "
                f"Gib keine Meinung vor, sondern zeige auf, worauf es ankommt.\n\n"
                f"Pro:\n{pro_response.text}\n\nKontra:\n{con_response.text}"
            )

            fazit_response = client.models.generate_content(model='gemini-2.5-flash', contents=fazit_prompt)
            st.markdown(fazit_response.text)
            st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Etwas hat nicht geklappt: {e}")
