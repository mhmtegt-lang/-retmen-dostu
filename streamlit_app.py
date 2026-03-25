import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# Sayfa Ayarları
st.set_page_config(page_title="ÖdevAI - Ücretsiz", layout="wide")

# API Anahtarı Girişi
with st.sidebar:
    st.title("⚙️ Ayarlar")
    api_key = st.text_input("Google API Key (Gemini)", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("Lütfen AI Studio'dan aldığınız ücretsiz anahtarı girin.")
    st.stop()

# Model Ayarı (Gemini 1.5 Flash - Hızlı ve Ücretsiz)
model = genai.GenerativeModel('gemini-1.5-flash')

# Session State
if 'reference_key' not in st.session_state: st.session_state.reference_key = None
if 'results' not in st.session_state: st.session_state.results = []

st.title("📚 ÖdevAI (Ücretsiz Sürüm)")

tab1, tab2, tab3 = st.tabs(["1. Cevap Anahtarı", "2. Ödevleri Kontrol Et", "3. Rapor"])

with tab1:
    master_file = st.file_uploader("Boş ödev sayfasını yükleyin", type=['jpg', 'png'])
    if master_file and st.button("🔍 Soruları Çöz"):
        img = Image.open(master_file)
        # Gemini'ye görseli ve promptu gönderiyoruz
        prompt = "Bu ödev sayfasındaki soruları çöz ve YALNIZCA şu JSON formatında dön: {'subject': '...', 'questions': [{'id': 1, 'text': '...', 'final_answer': '...'}]}"
        response = model.generate_content([prompt, img])
        
        # JSON verisini ayıklama
        res_text = response.text.replace('```json', '').replace('```', '')
        st.session_state.reference_key = json.loads(res_text)
        st.success("Cevap anahtarı hazır!")

# Not: Diğer sekmelerdeki mantığı da benzer şekilde model.generate_content ile güncelleyebilirsiniz.
