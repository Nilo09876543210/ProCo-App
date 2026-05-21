import streamlit as st
from duckduckgo_search import DDGS
from google import genai
from google.genai import types

# 1. App-Einrichtung & Webseiten-Design
st.set_page_config(
    page_title="ProCo - Der Meinungs-Debattierer",
    page_icon="⚖️",
    layout="wide"
)

# Schickes Design für die Pro/Kontra-Boxen (CSS)
st.markdown("""
    <style>
    .main-title { font-size: 3rem; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1.2rem; text-align: center; color: #4B5563; margin-bottom: 2rem; }
    .pro-box { background-color: #E6F4EA; padding: 20px; border-radius: 12px; border-left: 5px solid #137333; margin-bottom: 15px; }
    .con-box { background-color: #FCE8E6; padding: 20px; border-radius: 12px; border-left: 5px solid #C5221F; margin-bottom: 15px; }
    .fazit-box { background-color: #F1F3F4; padding: 25px; border-radius: 12px; border-top: 5px solid #3C4043; margin-top: 25px; }
    </style>
""", unsafe_allow_html=True)

# Titel auf der Webseite anzeigen
st.markdown('<div class="main-title">⚖️ ProCo</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Zwei Perspektiven. Aktuelle Fakten. Deine Meinungsbildung.</div>', unsafe_allow_html=True)

# Das große Eingabefeld für die Frage
user_input = st.text_input(
    "Gib eine These oder Fragestellung ein:",
    placeholder="z. B. Sollte das Schulsystem in Deutschland reformiert werden?",
)

# Funktion: Durchsucht das Internet nach aktuellen Infos zum Thema
def get_web_context(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=4)]
            return "\n\n".join(results)
    except Exception:
        return "Keine aktuellen Webdaten gefunden. Nutze internes Wissen."

# Wenn der Nutzer etwas eingegeben hat, startet die Magie
if user_input:
    # Versuche den API-Key sicher aus den Streamlit Secrets zu laden
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Fehler: Kein Gemini API-Key in den Streamlit Secrets gefunden! Bitte trage ihn in den Einstellungen ein.")
        st.stop()

    with st.spinner("Durchsuche das Web nach aktuellen Fakten und lasse die Bots debattieren..."):
        try:
            # 1. Live-Daten aus dem Web holen
            search_context = get_web_context(user_input)
            
            # 2. KI-Verbindung aufbauen
            client = genai.Client(api_key=api_key)
            base_prompt = f"Thema: {user_input}\n\nAktueller Web-Kontext:\n{search_context}\n\n"
            
            # Anweisungen für den Pro-Bot
            pro_instruction = (
                "Du bist ein analytischer Debatten-Bot, der AUSSCHLIESSLICH starke Pro-Argumente liefert. "
                "Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch in übersichtlichen Bulletpoints."
            )
            
            # Anweisungen für den Kontra-Bot
            con_instruction = (
                "Duatischer Debatten-Bot, der AUSSCHLIESSLICH starke Kontra-Argumente liefert. "
                "Nutze die Web-Daten für aktuelle Fakten. Antworte auf Deutsch in übersichtlichen Bulletpoints."
            )
            
            # 3. Beide Bots antworten lassen (gemini-2.5-flash ist super schnell)
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
            
            # Spalten auf der Webseite erstellen
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="pro-box"><h3>🟢 Pro-Argumente</h3></div>', unsafe_allow_html=True)
                st.markdown(pro_response.text)
                
            with col2:
                st.markdown('<div class="con-box"><h3>🔴 Kontra-Argumente</h3></div>', unsafe_allow_html=True)
                st.markdown(con_response.text)
            
            # 4. Das neutrale Fazit erstellen
            st.markdown("---")
            st.markdown('<div class="fazit-box"><h3>🤖 Impuls zur Meinungsbildung (Neutrales Fazit)</h3>', unsafe_allow_html=True)
            
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
