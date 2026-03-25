import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import time

# Sayfa Genişliği ve Başlık
st.set_page_config(page_title="ÖdevAI | Öğretmen Asistanı", layout="wide")

# --- STYLE ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: API AYARLARI ---
with st.sidebar:
    st.title("⚙️ Ayarlar")
    api_key = st.text_input("Google Gemini API Key", type="password", help="AI Studio'dan aldığınız ücretsiz anahtarı buraya yapıştırın.")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            # Modeli en güncel haliyle tanımlıyoruz
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            st.success("API Bağlantısı Başarılı!")
        except Exception as e:
            st.error(f"Bağlantı Hatası: {e}")

    st.info("Bu uygulama ücretsiz Gemini API katmanını kullanır.")

# --- SESSION STATE (Veri Saklama) ---
if 'reference_key' not in st.session_state:
    st.session_state.reference_key = None
if 'results' not in st.session_state:
    st.session_state.results = []

# --- ANA EKRAN ---
st.title("📚 ÖdevAI: Akıllı Ödev Kontrolü")
st.write("Öğrencilerinizin ödevlerini fotoğraflardan saniyeler içinde analiz edin.")

if not api_key:
    st.warning("Lütfen sol taraftaki ayarlardan API anahtarınızı girerek başlayın.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["1️⃣ Cevap Anahtarı Oluştur", "2️⃣ Öğrenci Kağıtlarını Analiz Et", "3️⃣ Sınıf Raporu"])

# --- TAB 1: CEVAP ANAHTARI ---
with tab1:
    st.header("Referans Ödev Sayfası")
    master_file = st.file_uploader("Boş ödevin veya sizin çözdüğünüz anahtarın fotoğrafını yükleyin", type=['jpg', 'jpeg', 'png'], key="master")
    
    if master_file:
        img_master = Image.open(master_file)
        st.image(img_master, caption="Yüklenen Referans", width=400)
        
        if st.button("🔍 Soruları Analiz Et"):
            with st.spinner("Gemini soruları çözüyor ve anahtar oluşturuyor..."):
                prompt = """Sen uzman bir öğretmensin. Görseldeki tüm soruları tanımla ve çöz. 
                Yanıtını YALNIZCA aşağıdaki JSON formatında ver, başka metin ekleme:
                {
                    "subject": "Ders Adı",
                    "total_questions": 5,
                    "questions": [
                        {"id": 1, "text": "soru metni", "final_answer": "cevap", "steps": ["adım 1", "adım 2"]}
                    ]
                }"""
                try:
                    response = model.generate_content([prompt, img_master])
                    # Markdown temizliği
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    st.session_state.reference_key = json.loads(clean_json)
                    st.success("Cevap anahtarı başarıyla oluşturuldu!")
                    st.json(st.session_state.reference_key)
                except Exception as e:
                    st.error(f"Analiz sırasında hata oluştu: {e}")

# --- TAB 2: ÖĞRENCİ ANALİZİ ---
with tab2:
    if not st.session_state.reference_key:
        st.error("Lütfen önce bir cevap anahtarı oluşturun.")
    else:
        st.header("Öğrenci Kağıtları")
        student_files = st.file_uploader("Öğrenci kağıtlarını toplu olarak yükleyin", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if student_files and st.button("🚀 Analizi Başlat"):
            results = []
            progress_bar = st.progress(0)
            
            for i, file in enumerate(student_files):
                img_student = Image.open(file)
                student_name = file.name.split(".")[0]
                
                analysis_prompt = f"""
                Aşağıdaki cevap anahtarına göre öğrenci kağıdını kontrol et:
                Cevap Anahtarı: {json.dumps(st.session_state.reference_key)}
                
                Öğrencinin çözüm yollarını incele, işlem hatası varsa hangi adımda olduğunu belirt.
                Yanıtı YALNIZCA bu JSON formatında ver:
                {{
                    "student_name": "{student_name}",
                    "score": 85,
                    "feedback": "Kısa genel geri bildirim",
                    "details": [
                        {{"question_id": 1, "is_correct": true, "error_desc": "yok"}}
                    ]
                }}
                """
                try:
                    res = model.generate_content([analysis_prompt, img_student])
                    clean_res = res.text.replace('```json', '').replace('```', '').strip()
                    results.append(json.loads(clean_res))
                except:
                    results.append({"student_name": student_name, "score": 0, "feedback": "Analiz edilemedi."})
                
                progress_bar.progress((i + 1) / len(student_files))
                time.sleep(1) # API limitlerine takılmamak için kısa bekleme
            
            st.session_state.results = results
            st.success(f"{len(results)} öğrenci kağıdı başarıyla kontrol edildi!")

# --- TAB 3: RAPOR ---
with tab3:
    if not st.session_state.results:
        st.info("Henüz analiz edilmiş bir kağıt yok.")
    else:
        st.header("📊 Sınıf Başarı Raporu")
        
        avg_score = sum(r['score'] for r in st.session_state.results) / len(st.session_state.results)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Sınıf Ortalaması", f"%{avg_score:.1f}")
        col2.metric("En Yüksek Puan", f"%{max(r['score'] for r in st.session_state.results)}")
        col3.metric("Kontrol Edilen", len(st.session_state.results))
        
        st.divider()
        
        for res in st.session_state.results:
            with st.expander(f"{res['student_name']} - Puan: {res['score']}"):
                st.write(f"**Geri Bildirim:** {res['feedback']}")
                if 'details' in res:
                    for d in res['details']:
                        icon = "✅" if d['is_correct'] else "❌"
                        st.write(f"{icon} Soru {d['question_id']}: {d.get('error_desc', '')}")
