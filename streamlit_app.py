import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time
import re

# Sayfa Ayarları
st.set_page_config(page_title="ÖdevAI | Detaylı Çözüm", layout="wide", page_icon="📝")

def clean_json_string(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    api_key = st.text_input("Google API Key", type="password")
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = "gemini-2.5-flash" if "gemini-2.5-flash" in models else models[0]
            selected_model = st.selectbox("Model", models, index=models.index(target))
            model = genai.GenerativeModel(model_name=selected_model)
            st.success("Bağlantı Aktif")
        except Exception as e:
            st.error(f"Hata: {e}")

# --- SESSION STATE ---
if 'ref_key' not in st.session_state: st.session_state.ref_key = None

st.title("📚 Adım Adım Ödev Analiz Sistemi")

if not api_key:
    st.info("Devam etmek için API anahtarınızı girin.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🎯 1. Cevap Anahtarı (Detaylı)", "🔍 2. Öğrenci Analizi", "📊 3. Sınıf Raporu"])

# --- TAB 1: DETAYLI CEVAP ANAHTARI ---
with tab1:
    master_file = st.file_uploader("Ödev sayfasını yükleyin", type=['jpg', 'jpeg', 'png'])
    
    if master_file:
        img = Image.open(master_file)
        st.image(img, caption="Referans Görsel", width=300)
        
        if st.button("Soruları Adım Adım Çöz"):
            with st.spinner("Gemini detaylı çözümleri hazırlıyor..."):
                # GÜNCELLENEN PROMPT: Adım adım çözüm istiyoruz
                prompt = """
                Görseldeki tüm matematik sorularını tanımla ve her birini bir öğretmen gibi adım adım çöz. 
                Özellikle kesirleri ondalığa çevirme veya payda eşitleme gibi işlem basamaklarını açıkça belirt.
                Yanıtı YALNIZCA şu JSON formatında dön:
                {
                    "subject": "Ders Adı",
                    "total_questions": 9,
                    "questions": [
                        {
                            "id": 1,
                            "text": "soru metni",
                            "steps": ["1. adım açıklaması", "2. adım açıklaması"],
                            "final_answer": "sonuç"
                        }
                    ]
                }
                """
                try:
                    response = model.generate_content([prompt, img])
                    json_data = clean_json_string(response.text)
                    st.session_state.ref_key = json.loads(json_data)
                    st.success("Detaylı cevap anahtarı hazır!")
                except Exception as e:
                    st.error(f"Hata: {e}")

    # Çözümleri ekranda güzelce gösterelim
    if st.session_state.ref_key:
        st.divider()
        st.subheader(f"📖 {st.session_state.ref_key.get('subject', 'Ödev')} Çözüm Anahtarı")
        for q in st.session_state.ref_key['questions']:
            with st.expander(f"Soru {q['id']}: {q['text']} (Cevap: {q['final_answer']})"):
                st.write("**İşlem Basamakları:**")
                for i, step in enumerate(q.get('steps', []), 1):
                    st.write(f"{i}. {step}")

# (Tab 2 ve Tab 3 önceki kodlardaki gibi devam edebilir...)
