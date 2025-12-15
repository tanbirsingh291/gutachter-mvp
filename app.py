
import streamlit as st
import google.generativeai as genai
import tempfile
import os

# Seite konfigurieren
st.set_page_config(page_title="Kfz-Gutachter AI (Gemini)", page_icon="🚗")

# Header
st.title("🚗 {g}ai-solutions: Gutachter-Assistent")
st.caption("Powered by Google Gemini 1.5 Flash")

# API Key Setup
# Lokal: Entweder in .env oder direkt hier (für lokale Tests)
# In Streamlit Cloud: In den Secrets als GOOGLE_API_KEY hinterlegen
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Fallback für lokales Testen (nicht empfohlen für Git-Upload!)
    api_key = "DEIN_GEMINI_API_KEY_HIER_EINFÜGEN"

if not api_key:
    st.error("Bitte API Key hinterlegen.")
    st.stop()

genai.configure(api_key=api_key)

# Modell wählen (Flash ist super schnell und günstig)
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. Audio Aufnahme
audio_value = st.audio_input("Schaden jetzt einsprechen (Mikrofon)")

if audio_value:
    st.info("Audio wird verarbeitet... Gemini hört zu 🧠")
    
    try:
        # Streamlit liefert Bytes, Gemini braucht eine Datei. 
        # Wir speichern temporär zwischen.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_file_path = tmp_file.name

        # Datei zu Google hochladen
        myfile = genai.upload_file(tmp_file_path)
        
        # Der Prompt für den Gutachter-Stil
        prompt = """
        Du bist ein erfahrener Kfz-Sachverständiger in Deutschland.
        Höre dir diese Audioaufnahme genau an. Sie enthält Notizen zu einem Unfallschaden.
        
        Deine Aufgabe:
        Erstelle daraus ein professionelles, strukturiertes Gutachten.
        
        Anforderungen:
        1. Formuliere alles im Passiv und im neutralen Sachverständigen-Stil (z.B. "Der Kotflügel weist eine Verformung auf" statt "Der Kotflügel ist kaputt").
        2. Verwende Fachbegriffe (Lackierung, Instandsetzung, Erneuerung).
        3. Strukturiere das Ergebnis in:
           - Fahrzeugdaten (falls im Audio genannt)
           - Schadensbeschreibung (detailliert)
           - Reparaturempfehlung
        
        Gib NUR das fertige Gutachten aus, kein Vorgeplänkel.
        """

        # Generierung starten (Audio + Text Prompt)
        with st.spinner("Gutachten wird geschrieben..."):
            response = model.generate_content([prompt, myfile])
            
        # Ergebnis anzeigen
        st.subheader("📝 Generierter Bericht")
        st.markdown(response.text)
        
        # Download
        st.download_button("Bericht speichern", response.text, file_name="gutachten_gemini.md")

        # Aufräumen (Temporäre Datei löschen)
        os.unlink(tmp_file_path)

    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
