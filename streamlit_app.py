import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time

# Sayfa Ayarları
st.set_page_config(page_title="ÖdevAI | Sorunsuz Sürüm", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    selected_model_name = "gemini-1.5-flash" # Varsayılan
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Mevcut modelleri çekiyoruz
            models = [m.name.replace('models/', '') for m in genai.list_models() 
                      if 'generateContent' in m.supported_generation_methods]
            
            selected_model_name = st.selectbox("Çalışan Bir Model Seçin", models, 
                                               index=models.index("gemini-1.5-flash") if "gemini-1.5-flash" in models else 0)
            st.success("API Bağlantısı Aktif!")
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")

# Seçilen modelle nesneyi oluştur
if api_key:
    model = genai.GenerativeModel(model_name=selected_model_name)

# --- SESSION STATE ---
if 'reference_key' not in st.session_state: st.session_state.reference_key = None
if 'results' not in st.session_state: st.session_state.results = []

st.title("📚 ÖdevAI Kontrol Sistemi")

if not api_key:
    st.warning("Lütfen sol menüden API anahtarınızı girin.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["1️⃣ Cevap Anahtarı", "2️⃣ Analiz", "3️⃣ Rapor"])

# --- TAB 1 ---
with tab1:
    master_file = st.file_uploader("Referans Ödev Fotoğrafı", type=['jpg', 'jpeg', 'png'])
    if master_file and st.button("🔍 Soruları Tanımla"):
        with st.spinner("Analiz ediliyor..."):
            img = Image.open(master_file)
            prompt = "Görseldeki soruları çöz ve YALNIZCA şu JSON formatında dön: {'subject': '...', 'total_questions': 5, 'questions': [{'id': 1, 'text': '...', 'final_answer': '...'}]}"
            try:
                # Modeli çağırırken hata kontrolü
                response = model.generate_content([prompt, img])
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.reference_key = json.loads(res_text)
                st.success(f"Başarılı! Model: {selected_model_name}")
                st.json(st.session_state.reference_key)
            except Exception as e:
                st.error(f"Hata: {e}. Lütfen yan menüden başka bir model seçmeyi deneyin.")

# --- TAB 2 ve 3 (Önceki kodla aynı mantıkta devam eder) ---
