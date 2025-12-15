import streamlit as st
import google.generativeai as genai
import tempfile
import os
import traceback

st.set_page_config(page_title="Debug Modus", page_icon="🛠️")
st.title("🛠️ Diagnose-Modus")

# SCHRITT 1: API Key prüfen
st.subheader("1. API Key Check")
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    # Wir zeigen nur die ersten 4 Zeichen zur Sicherheit
    st.success(f"✅ Key gefunden: {api_key[:4]}...*******")
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Kein API Key in den Secrets gefunden!\nFehler: {e}")
    st.stop()

# SCHRITT 2: Google Verbindung testen (nur Text)
st.subheader("2. Google Verbindung (Text)")
if st.button("Verbindung testen"):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Antworte nur mit dem Wort: 'Verbunden'")
        st.success(f"✅ Google antwortet: {response.text}")
    except Exception as e:
        st.error(f"❌ Google Verbindung fehlgeschlagen!")
        st.code(traceback.format_exc()) # Zeigt den genauen Fehler

# SCHRITT 3: Audio Test
st.subheader("3. Audio & Verarbeitung")
audio_value = st.audio_input("Sprich etwas kurz ein...")

if audio_value:
    st.info("Audio empfangen. Sende an Google...")
    try:
        # Temporäre Datei anlegen
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_file_path = tmp_file.name
        
        # Hochladen
        myfile = genai.upload_file(tmp_file_path)
        
        # Generieren
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(["Was wurde gesagt?", myfile])
        
        st.success("✅ Erfolg!")
        st.write(response.text)
        
        # Aufräumen
        os.unlink(tmp_file_path)
        
    except Exception as e:
        st.error("❌ Fehler bei der Audio-Verarbeitung:")
        # DAS HIER IST WICHTIG: Es zeigt dir den wahren Grund
        st.code(traceback.format_exc())
