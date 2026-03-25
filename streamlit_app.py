import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time
import re

# Sayfa Ayarları
st.set_page_config(page_title="ÖdevAI | Profesyonel Kontrol", layout="wide", page_icon="📝")

# --- YARDIMCI FONKSİYONLAR ---
def clean_json_string(text):
    """AI yanıtındaki JSON harici metinleri temizler."""
    try:
        # JSON bloğunu bulmak için regex kullanıyoruz
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group(0)
        return text
    except:
        return text

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Kurulum")
    api_key = st.text_input("Google API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            models = [m.name.replace('models/', '') for m in genai.list_models() 
                      if 'generateContent' in m.supported_generation_methods]
            # Senin ekranında çalışan 'gemini-2.5-flash' modelini öncelikli seçiyoruz
            target_model = "gemini-2.5-flash" if "gemini-2.5-flash" in models else models[0]
            selected_model = st.selectbox("Model Seçimi", models, index=models.index(target_model))
            model = genai.GenerativeModel(model_name=selected_model)
            st.success("Bağlantı Tamam!")
        except Exception as e:
            st.error(f"API Hatası: {e}")

# --- SESSION STATE ---
if 'ref_key' not in st.session_state: st.session_state.ref_key = None
if 'results' not in st.session_state: st.session_state.results = []

st.title("📚 Akıllı Ödev Kontrol Sistemi")

if not api_key:
    st.info("Devam etmek için sol tarafa API anahtarınızı girin.")
    st.stop()

# Sekmeler
tab1, tab2, tab3 = st.tabs(["🎯 1. Cevap Anahtarı", "🔍 2. Öğrenci Analizi", "📊 3. Sınıf Raporu"])

# --- TAB 1: CEVAP ANAHTARI ---
with tab1:
    st.subheader("Ödev Sayfasını Tanımlama")
    master_file = st.file_uploader("Kitap sayfasını veya çözümlü anahtarı yükleyin", type=['jpg', 'jpeg', 'png'])
    
    if master_file:
        img = Image.open(master_file)
        st.image(img, caption="Referans Görsel", width=350)
        
        if st.button("Soruları Çöz ve Anahtar Oluştur"):
            with st.spinner("Yapay zeka soruları analiz ediyor..."):
                prompt = """Bu ödevdeki tüm soruları çöz. Yanıtı YALNIZCA şu JSON formatında ver:
                { "subject": "ders", "total_questions": 9, "questions": [{"id": 1, "text": "...", "final_answer": "..."}] }"""
                try:
                    response = model.generate_content([prompt, img])
                    json_data = clean_json_string(response.text)
                    st.session_state.ref_key = json.loads(json_data)
                    st.success("Cevap anahtarı oluşturuldu! Şimdi '2. Öğrenci Analizi' sekmesine geçebilirsiniz.")
                    st.json(st.session_state.ref_key)
                except Exception as e:
                    st.error(f"Cevap anahtarı oluşturulurken hata: {e}")

# --- TAB 2: ANALİZ ---
with tab2:
    if not st.session_state.ref_key:
        st.warning("Lütfen önce 1. sekmeden cevap anahtarını oluşturun.")
    else:
        st.subheader("Öğrenci Kağıtlarını Yükleyin")
        files = st.file_uploader("Öğrenci fotoğraflarını seçin (Birden fazla seçebilirsiniz)", 
                                 type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if files and st.button("Analizi Başlat"):
            st.session_state.results = [] # Eski sonuçları temizle
            progress = st.progress(0)
            
            for i, f in enumerate(files):
                student_img = Image.open(f)
                st.write(f"Kontrol ediliyor: {f.name}")
                
                # Özel eğitim odaklı analiz promptu
                analysis_prompt = f"""
                Cevap Anahtarı: {json.dumps(st.session_state.ref_key)}
                Bu öğrenci kağıdını kontrol et. Yanlış cevap varsa, hatanın nedenini (işlem hatası, kavram yanılgısı vb.) açıkla.
                Yanıtı YALNIZCA şu JSON formatında ver:
                {{
                    "student_name": "{f.name.split('.')[0]}",
                    "score": 0,
                    "feedback": "...",
                    "details": [{"q_id": 1, "is_correct": true, "note": "..."}]
                }}
                """
                try:
                    res = model.generate_content([analysis_prompt, student_img])
                    clean_res = clean_json_string(res.text)
                    st.session_state.results.append(json.loads(clean_res))
                except Exception as e:
                    st.error(f"{f.name} analizi başarısız: {e}")
                
                progress.progress((i + 1) / len(files))
                time.sleep(1) # API limitini korumak için

            st.success("Tüm ödevler kontrol edildi! '3. Sınıf Raporu' sekmesine bakabilirsiniz.")

# --- TAB 3: RAPOR ---
with tab3:
    if not st.session_state.results:
        st.info("Henüz analiz edilmiş bir öğrenci kağıdı yok.")
    else:
        st.subheader("Sınıf Genel Durumu")
        results_df = [{"İsim": r['student_name'], "Puan": r['score'], "Geri Bildirim": r['feedback']} for r in st.session_state.results]
        st.table(results_df)
        
        # Detaylı İnceleme
        st.divider()
        st.subheader("Bireysel Hata Analizleri")
        for r in st.session_state.results:
            with st.expander(f"Öğrenci: {r['student_name']} - Detaylar"):
                for d in r['details']:
                    durum = "✅" if d['is_correct'] else "❌"
                    st.write(f"{durum} **Soru {d['q_id']}:** {d.get('note', '')}")
