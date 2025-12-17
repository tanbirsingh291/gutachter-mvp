import streamlit as st
import google.generativeai as genai
import tempfile
import os
from fpdf import FPDF
import datetime

# --- 1. KONFIGURATION & DESIGN ---
st.set_page_config(page_title="ProGutachter AI", page_icon="🚗", layout="wide")

st.title("🚗 {g}ai-solutions: Profi-Gutachten Generator")
st.markdown("### Automatische Erstellung nach DAT/Audatex-Standard")

# --- 2. API SETUP ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("❌ Fehler: API Key fehlt in den Streamlit Secrets.")
    st.stop()

genai.configure(api_key=api_key)

# --- 3. HELFER: PDF GENERATOR KLASSE ---
class GutachtenPDF(FPDF):
    def header(self):
        # Hier könnte dein Logo stehen
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'KFZ-SCHADENGUTACHTEN', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Seite {self.page_no()}/{{nb}} - Generiert mit gai-solutions', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255) # Hellblau hinterlegt wie im Muster oft üblich
        self.cell(0, 6, f'{label}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        # Umlaute fixen für FPDF (Latin-1)
        body = body.replace('’', "'").replace('„', '"').replace('“', '"')
        self.multi_cell(0, 5, body)
        self.ln()

# --- 4. INTELLIGENTE MODELL-SUCHE ---
@st.cache_resource
def get_available_model():
    # Wir nutzen Flash für Geschwindigkeit, aber Pro wäre für komplexe Formatierung besser
    return 'models/gemini-1.5-flash'

model = genai.GenerativeModel(get_available_model())

# --- 5. BENUTZEROBERFLÄCHE (INPUT) ---
col1, col2 = st.columns(2)

with col1:
    st.info("🎙️ Option A: Diktieren")
    audio_mic = st.audio_input("Aufnahme starten")

with col2:
    st.info("📂 Option B: Datei")
    audio_upload = st.file_uploader("Upload (MP3, WAV)", type=["mp3", "wav", "m4a", "ogg"])

audio_value = audio_mic if audio_mic else audio_upload

# --- 6. VERARBEITUNG ---
if audio_value:
    st.success("Audio empfangen. Generiere Gutachten-Struktur...")
    
    try:
        suffix = ".wav"
        if audio_upload:
            suffix = os.path.splitext(audio_upload.name)[1]
            if suffix == "": suffix = ".wav"
            
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_value.read())
            tmp_file_path = tmp_file.name

        myfile = genai.upload_file(tmp_file_path)
        
        # --- DER NEUE, VERBESSERTE PROMPT ---
        # Dieser Prompt zwingt die KI in die Struktur des Mustergutachtens
        prompt = """
        Du bist ein professioneller Kfz-Sachverständiger in Deutschland.
        Deine Aufgabe ist es, aus dem Audio-Diktat den Textteil eines offiziellen Haftpflichtgutachtens zu erstellen.
        
        Orientiere dich strikt an folgender Struktur (wie in Branchenstandards üblich):

        1. ZUSAMMENFASSUNG
           - Erwähne kurz das Fahrzeug und die Art des Schadens.
           - Falls Zahlen (Reparaturkosten, Restwert) genannt wurden, liste sie hier auf. Falls nicht, schreibe "Wird kalkuliert".

        2. ALLGEMEINE ANGABEN ZUR BESICHTIGUNG
           - Ort, Datum, Uhrzeit (falls im Audio, sonst "gemäß Auftrag").
           - Besichtigungsbedingungen (z.B. "ausreichend beleuchtet").

        3. FAHRZEUGDATEN & AUSSTATTUNG
           - Fahrzeugtyp, Hersteller, Modell.
           - VIN, Kennzeichen, Laufleistung (falls genannt).
           - Wesentliche Ausstattungsmerkmale (Leder, Navi, Felgen etc.).

        4. ALTSCHÄDEN / VORSCHÄDEN
           - Liste explizit genannte Altschäden auf.
           - Wenn nichts genannt, schreibe: "Augenscheinlich keine unreparierten Altschäden erkennbar."

        5. SCHADENSBESCHREIBUNG (Der wichtigste Teil)
           - Beschreibe den Schaden detailliert im Passiv (z.B. "Der Kotflügel vorne rechts wurde eingedrückt...").
           - Nutze technische Fachbegriffe (Sicke, Stauchung, Spaltmaße, Lackabrieb).
           - Gehe Bauteil für Bauteil durch (Stoßfänger, Kotflügel, Scheinwerfer, Tür, etc.).

        6. REPARATURWEG
           - Was muss getan werden? (Erneuern, Instandsetzen, Lackieren).
           - Nenne eventuelle Beilackierungen angrenzender Teile.

        WICHTIG:
        - Schreibe keine Einleitung ("Hier ist das Gutachten"). Starte direkt mit Punkt 1.
        - Nutze Markdown-Formatierung für Überschriften (z.B. # 1. ZUSAMMENFASSUNG).
        - Tonfall: Sachlich, neutral, juristisch präzise.
        """

        with st.spinner("KI analysiert Schaden und schreibt Bericht..."):
            response = model.generate_content([prompt, myfile])
            report_text = response.text
        
        # --- 7. ERGEBNIS ANZEIGEN & PDF ERSTELLEN ---
        col_res1, col_res2 = st.columns([1, 1])
        
        with col_res1:
            st.subheader("Vorschau (Text)")
            st.markdown(report_text)

        # PDF Generierung
        pdf = GutachtenPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # Wir parsen das Markdown simpel, um es ins PDF zu bekommen
        lines = report_text.split('\n')
        for line in lines:
            # Encoding fix für typische Sonderzeichen
            safe_line = line.encode('latin-1', 'replace').decode('latin-1')
            
            if line.startswith("# "):
                pdf.chapter_title(safe_line.replace("# ", "").replace("*", ""))
            elif line.startswith("## "):
                pdf.chapter_title(safe_line.replace("## ", "").replace("*", ""))
            else:
                if line.strip() != "":
                    pdf.chapter_body(safe_line.replace("*", ""))

        # Temporäres PDF speichern
        pdf_output_path = os.path.join(tempfile.gettempdir(), "gutachten.pdf")
        pdf.output(pdf_output_path)

        with col_res2:
            st.subheader("📄 Fertiges PDF")
            st.success("Das Gutachten wurde formatiert.")
            
            with open(pdf_output_path, "rb") as f:
                st.download_button(
                    label="⬇️ PDF Gutachten herunterladen",
                    data=f,
                    file_name=f"Gutachten_{datetime.date.today()}.pdf",
                    mime="application/pdf"
                )

        # Aufräumen
        os.unlink(tmp_file_path)

    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
