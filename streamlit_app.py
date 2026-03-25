import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="ÖdevAI | Özel Eğitim Asistanı", layout="wide", page_icon="📚")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    api_key = st.text_input("Google Gemini API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for m in genai.list_models() 
                      if 'generateContent' in m.supported_generation_methods]
            # Senin ekranında çalışan modeli varsayılan yapıyoruz
            default_model = "gemini-2.5-flash" if "gemini-2.5-flash" in models else models[0]
            selected_model_name = st.selectbox("Çalışan Modeli Seçin", models, index=models.index(default_model))
            st.success("Bağlantı Aktif!")
            model = genai.GenerativeModel(model_name=selected_model_name)
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")

# --- SESSION STATE ---
if 'ref_key' not in st.session_state: st.session_state.ref_key = None
if 'results' not in st.session_state: st.session_state.results = []

st.title("📚 ÖdevAI: Akıllı Ödev Kontrolü")

if not api_key:
    st.warning("Lütfen sol menüden API anahtarınızı girin.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["1️⃣ Cevap Anahtarı", "2️⃣ Öğrenci Analizi", "3️⃣ Sınıf Raporu"])

# --- TAB 1: CEVAP ANAHTARI ---
with tab1:
    master_file = st.file_uploader("Kitap/Ödev Fotoğrafı Yükle", type=['jpg', 'jpeg', 'png'], key="m_up")
    if master_file and st.button("🔍 Soruları ve Çözümleri Tanımla"):
        with st.spinner("Sorular analiz ediliyor..."):
            img = Image.open(master_file)
            prompt = """Bu ödevdeki soruları çöz. Yanıtı YALNIZCA şu JSON formatında dön:
            { "subject": "ders adı", "total_questions": 5, "questions": [{"id": 1, "text": "...", "final_answer": "..."}] }"""
            try:
                response = model.generate_content([prompt, img])
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.ref_key = json.loads(res_text)
                st.success("Cevap anahtarı hazır!")
                st.json(st.session_state.ref_key)
            except Exception as e:
                st.error(f"Hata: {e}")

# --- TAB 2: ÖĞRENCİ ANALİZİ ---
with tab2:
    if not st.session_state.ref_key:
        st.info("Önce 1. sekmeden cevap anahtarı oluşturun.")
    else:
        st.header("Öğrenci Kağıtlarını Yükle")
        student_files = st.file_uploader("Öğrenci kağıtlarını seçin", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if student_files and st.button("🚀 Tümünü Analiz Et"):
            new_results = []
            progress_bar = st.progress(0)
            
            for i, file in enumerate(student_files):
                img_student = Image.open(file)
                st.write(f"Analiz ediliyor: {file.name}...")
                
                # ÖZEL EĞİTİM ODAKLI PROMPT
                analysis_prompt = f"""
                Sen uzman bir matematik ve özel eğitim öğretmenisin. 
                Referans Anahtar: {json.dumps(st.session_state.ref_key)}
                
                Görseldeki öğrenci ödevini kontrol et. 
                1. Sonuç doğru mu?
                2. Yanlışsa, hatanın türü nedir? (Basamak hatası, kavram yanılgısı, işlem hatası vb.)
                
                Yanıtı YALNIZCA şu JSON formatında dön:
                {{
                    "student_name": "{file.name.split('.')[0]}",
                    "score": 80,
                    "feedback": "Genel pedagojik dönüt",
                    "details": [
                        {{"q_id": 1, "is_correct": true, "error_type": "yok", "note": "..."}}
                    ]
                }}
                """
                try:
                    res = model.generate_content([analysis_prompt, img_student])
                    res_json = json.loads(res.text.replace('```json', '').replace('```', '').strip())
                    new_results.append(res_json)
                except:
                    st.warning(f"{file.name} analiz edilemedi.")
                
                progress_bar.progress((i + 1) / len(student_files))
                time.sleep(1.5) # Kota aşımı için kısa bekleme
            
            st.session_state.results = new_results
            st.success("Tüm analizler tamamlandı! Rapor sekmesine geçebilirsiniz.")

# --- TAB 3: SINIF RAPORU ---
with tab3:
    if not st.session_state.results:
        st.info("Henüz analiz edilmiş kağıt bulunmuyor.")
    else:
        st.header("📊 Sınıf Başarı Grafiği")
        df = pd.DataFrame(st.session_state.results)
        
        # Dashboard Metrikleri
        c1, c2, c3 = st.columns(3)
        c1.metric("Sınıf Ortalaması", f"%{df['score'].mean():.1f}")
        c2.metric("En Yüksek Puan", f"%{df['score'].max()}")
        c3.metric("Kağıt Sayısı", len(df))
        
        st.bar_chart(df.set_index('student_name')['score'])
        
        st.divider()
        st.subheader("📝 Bireysel Geri Bildirimler")
        for res in st.session_state.results:
            with st.expander(f"👤 {res['student_name']} - Puan: {res['score']}"):
                st.info(f"**Öğretmen Notu:** {res['feedback']}")
                for d in res['details']:
                    icon = "✅" if d['is_correct'] else "❌"
                    st.write(f"{icon} **Soru {d['q_id']}:** {d['note']}")
