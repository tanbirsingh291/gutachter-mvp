import streamlit as st
import google.generativeai as genai
import tempfile
import os

# --- 1. KONFIGURATION & DESIGN ---
st.set_page_config(page_title="Gutachter AI", page_icon="🚗")

st.title("🚗 {g}ai-solutions: Gutachter-Assistent")
st.write("Sprechen Sie den Schaden ein oder laden Sie eine Sprachmemo hoch.")

# --- 2. API SETUP ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("❌ Fehler: API Key fehlt in den Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. INTELLIGENTE MODELL-SUCHE (Hintergrund) ---
# Diese Funktion verhindert den "404 Model Not Found" Fehler,
# indem sie prüft, was dein Key wirklich darf.
@st.cache_resource
def get_available_model():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'flash' in m.name: # Bevorzuge das schnelle Flash-Modell
                    return m.name
        return 'models/gemini-1.5-flash' # Standard-Fallback
    except:
        return 'models/gemini-1.5-flash'

valid_model_name = get_available_model()
model = genai.GenerativeModel(valid_model_name)

# --- 4. BENUTZEROBERFLÄCHE (INPUT) ---
col1, col2 = st.columns(2)

with col1:
    audio_mic = st.audio_input("🎙️ Aufnahme starten")

with col2:
    audio_upload = st.file_uploader("📂 Datei hochladen", type=["mp3", "wav", "m4a", "ogg"])

# Wir nehmen das, was der Nutzer gerade nutzt
audio_value = audio_mic if audio_mic else audio_upload

# --- 5. VERARBEITUNG ---
if audio_value:
    st.success("Audio empfangen. Analyse läuft...")
    
    try:
        # Dateiendung für Gemini vorbereiten
        suffix = ".wav"
        if audio_upload:
            suffix = os.path.splitext(audio_upload.name)[1]
            if suffix == "": suffix = ".wav"
            
        # Temporäre Datei erstellen (Gemini braucht eine Datei, keinen Stream)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_file_path = tmp_file.name

        # Datei zu Google senden
        myfile = genai.upload_file(tmp_file_path)
        
        # Der Befehl an die KI
        prompt = """
        Du bist ein erfahrener Kfz-Sachverständiger in Deutschland. 
        Analysiere diese Audioaufnahme (Unfallschaden-Diktat).
        
        Erstelle daraus ein professionelles Gutachten mit folgender Struktur:
        1. Fahrzeugdaten (falls genannt)
        2. Schadensbeschreibung (Detailliert, Fachsprache nutzen, Passiv-Formulierungen wie "wurde beschädigt")
        3. Reparaturweg (Instandsetzung, Lackierung, Erneuerung)
        4. Zusammenfassung
        
        Wichtig: Schreibe sachlich, neutral und juristisch sauber.
        """

        # Generierung mit Lade-Animation
        with st.spinner("Ihr KI-Assistent erstellt das Gutachten..."):
            response = model.generate_content([prompt, myfile])
            
        # --- 6. ERGEBNIS ANZEIGEN ---
        st.divider()
        st.subheader("📝 Generierter Bericht")
        st.markdown(response.text)
        
        # Download Button für den Text
        st.download_button(
            label="💾 Bericht als Text speichern",
            data=response.text,
            file_name="gutachten_entwurf.md",
            mime="text/markdown"
        )
        
        # Aufräumen (Müll löschen)
        os.unlink(tmp_file_path)

    except Exception as e:
        st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
