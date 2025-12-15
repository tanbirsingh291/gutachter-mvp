import streamlit as st
import google.generativeai as genai
import tempfile
import os

st.set_page_config(page_title="Kfz-Gutachter AI", page_icon="🚗")
st.title("🚗 {g}ai-solutions: Gutachter-Assistent")

# 1. API Key Setup
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Fallback, falls du es lokal ohne Secrets testest
    st.error("Bitte API Key in Secrets hinterlegen.")
    st.stop()

genai.configure(api_key=api_key)

# --- NEU: AUTOMATISCHE MODELL-SUCHE ---
@st.cache_resource
def get_available_model():
    """Sucht automatisch ein verfügbares Modell für diesen Key."""
    try:
        # Wir fragen Google: Welche Modelle gibt es?
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Wir bevorzugen Flash (schnell)
                    return m.name
                if 'pro' in m.name:   # Fallback auf Pro
                    return m.name
        return 'models/gemini-pro' # Absoluter Notfall-Fallback
    except Exception as e:
        return None

# Wir holen uns das Modell, das WIRKLICH da ist
valid_model_name = get_available_model()

if not valid_model_name:
    st.error("❌ Fehler: Dein API-Key hat Zugriff auf KEINE Text-Modelle. Bitte erstelle einen neuen Key in Google AI Studio.")
    st.stop()
else:
    # Zeige ganz klein an, welches Modell er gefunden hat (zur Kontrolle)
    st.caption(f"Verbinde mit: `{valid_model_name}`")
    model = genai.GenerativeModel(valid_model_name)

# 2. UI: Audio Aufnahme oder Upload
st.info("💡 Tipp: Wenn das Mikrofon am Handy streikt, lade einfach eine Sprachmemo hoch.")
col1, col2 = st.columns(2)
with col1:
    audio_mic = st.audio_input("🎙️ Aufnahme starten")
with col2:
    audio_upload = st.file_uploader("📂 Datei hochladen", type=["mp3", "wav", "m4a", "ogg"])

audio_value = audio_mic if audio_mic else audio_upload

if audio_value:
    st.success("Audio empfangen! KI analysiert...")
    
    try:
        # Dateiendung bestimmen
        suffix = ".wav"
        if audio_upload:
            suffix = os.path.splitext(audio_upload.name)[1]
            if suffix == "": suffix = ".wav"
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_file_path = tmp_file.name

        # Upload zu Google
        myfile = genai.upload_file(tmp_file_path)
        
        prompt = """
        Du bist ein Kfz-Sachverständiger. 
        Erstelle aus dieser Audioaufnahme ein strukturiertes Gutachten 
        (Fahrzeugdaten, Schaden, Reparaturweg) im professionellen, passiven Sprachstil.
        """

        with st.spinner(f"KI schreibt Gutachten mit {valid_model_name}..."):
            response = model.generate_content([prompt, myfile])
            
        st.subheader("📝 Generierter Bericht")
        st.markdown(response.text)
        
        # Aufräumen
        os.unlink(tmp_file_path)

    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
