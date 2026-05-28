import streamlit as st
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# 1. App-Einrichtung & Webseiten-Design (Modern & Clean)
st.set_page_config(
    page_title="ProCo - KI Debatten-Plattform",
    page_icon="⚖️",
    layout="wide"
)

# Super schickes, modernes CSS-Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-title { 
        font-size: 3.5rem; 
        font-weight: 800; 
        background: linear-gradient(45deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center; 
        margin-bottom: 0.2rem; 
    }
    
    .subtitle { 
        font-size: 1.2rem; 
        text-align: center; 
        color: #6B7280; 
        margin-bottom: 3rem; 
    }
    
    .pro-card { 
        background-color: #F0FDF4; 
        padding: 24px; 
        border-radius: 16px; 
        border: 1px solid #DCFCE7;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px; 
    }
    
    .con-card { 
        background-color: #FEF2F2; 
        padding: 24px; 
        border-radius: 16px; 
        border: 1px solid #FEE2E2;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px; 
    }
    
    .fazit-card { 
        background-color: #F8FAFC; 
        padding: 30px; 
        border-radius: 16px; 
        border: 1px solid #E2E8F0; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        margin-top: 30px; 
    }
    
    h3 {
        font-weight: 600 !important;
        margin-top: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Titel auf der Webseite
st.markdown('<div class="main-title">⚖️ ProCo</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Zwei Perspektiven. Aktuelle Live-Fakten. Deine Meinungsbildung.</div>', unsafe_allow_html=True)

# --- NEU: EINSTELLUNGEN IN DER SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Einstellungen")
    # Schieberegler von 1 bis 8 Argumente (Standardmäßig eingestellt auf 4)
    anzahl_argumente = st.slider(
        "Anzahl der Argumente pro Seite:",
        min_value=1,
        max_value=8,
        value=4
    )
    st.write("---")
    st.caption("ProCo nutzt Echtzeit-Webdaten und Google Gemini 2.5.")

# Das große Eingabefeld für die Frage
user_input = st.text_input(
    "Gib eine These oder Fragestellung ein:",
    placeholder="z. B. Sollte die Vier-Tage-Woche flächendeckend eingeführt werden?",
)

# Funktion für die Internetsuche
def get_web_context(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=4)]
            return "\n\n".join(results)
    except Exception:
        return "Keine aktuellen Webdaten gefunden. Nutze internes Wissen."

# Wenn der Nutzer etwas eingegeben hat
if user_input:
    # API-Key aus Secrets laden
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Fehler: Kein Gemini API-Key in den Streamlit Secrets gefunden!")
        st.stop()

    with st.spinner("Durchsuche das Web und lasse die KIs debattieren..."):
        try:
            search_context = get_web_context(user_input)
            client = genai.Client(api_key=api_key)
            base_prompt = f"Thema: {user_input}\n\nAktueller Web-Kontext:\n{search_context}\n\n"

            # Anweisungen für die Bots (jetzt dynamisch mit der Anzahl der Argumente)
            pro_instruction = (
                f"Du bist ein analytischer Debatten-Bot, der AUSSCHLIESSLICH starke Pro-Argumente liefert. "
                f"Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch und liefere EXAKT {anzahl_argumente} "
                f"übersichtliche, prägnante Bulletpoints (keine Einleitung, kein Fazit)."
            )

            con_instruction = (
                f"Du bist ein analytischer Debatten-Bot, der AUSSCHLIESSLICH starke Kontra-Argumente liefert. "
                f"Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch und liefere EXAKT {anzahl_argumente} "
                f"übersichtliche, prägnante Bulletpoints (keine Einleitung, kein Fazit)."
            )

            # KI-Abfrage starten
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

            # Layout: Spalten für Pro und Kontra Cards
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f'<div class="pro-card"><h3 style="color: #16A34A;">🟢 Pro-Argumente ({anzahl_argumente})</h3>', unsafe_allow_html=True)
                st.markdown(pro_response.text)
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown(f'<div class="con-card"><h3 style="color: #DC2626;">🔴 Kontra-Argumente ({anzahl_argumente})</h3>', unsafe_allow_html=True)
                st.markdown(con_response.text)
                st.markdown('</div>', unsafe_allow_html=True)

            # Das neutrale Fazit am Ende
            st.markdown('<div class="fazit-card"><h3 style="color: #334155;">🤖 Impuls zur Meinungsbildung (Neutrales Fazit)</h3>', unsafe_allow_html=True)

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
