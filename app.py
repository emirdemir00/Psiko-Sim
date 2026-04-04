import streamlit as st
from openai import OpenAI
import time
import os
import io
from supabase import create_client, Client 
from streamlit_mic_recorder import mic_recorder
import requests
from streamlit_lottie import st_lottie

# --- 0. DİL SÖZLÜĞÜ (Metrikler dahil edildi) ---
LANG_DICT = {
    "tr": {
        "title": "🧠 Psiko-Sim Laboratuvarı",
        "subtitle": "Psikolog adayları için geliştirilmiş sanal danışan simülasyonu",
        "sidebar_title": "🗂 Danışan Kütüphanesi",
        "expander_about": "ℹ️ Proje Hakkında",
        "expander_admin": "🛠️ Yetkili Paneli (Gizli)",
        "chat_placeholder": "Terapist olarak sorunuzu yazın...",
        "auth_label": "Uzman Şifresi:",
        "login_btn": "Giriş Yap",
        "reset_btn": "Sohbeti Sıfırla",
        "welcome_msg": "👋 Sisteme başarıyla giriş yaptınız. Seansa başlamak için sol menüden bir danışan dosyası seçin.",
        "m1_label": "Sistem Durumu", "m1_val": "Çevrimiçi", "m1_delta": "Bağlantı Hazır",
        "m2_label": "Kayıtlı Vaka Sayısı", "m2_unit": "Danışan",
        "m3_label": "Klinik Oda Durumu", "m3_val": "Müsait", "m3_delta": "Görüşmeye Hazır"
    },
    "en": {
        "title": "🧠 Psycho-Sim Lab",
        "subtitle": "Virtual patient simulation developed for psychologist candidates",
        "sidebar_title": "🗂 Patient Library",
        "expander_about": "ℹ️ About Project",
        "expander_admin": "🛠️ Admin Panel (Hidden)",
        "chat_placeholder": "Type your question as a therapist...",
        "auth_label": "Expert Password:",
        "login_btn": "Login",
        "reset_btn": "Reset Chat",
        "welcome_msg": "👋 Successfully logged in. Please select a patient file from the sidebar to start the session.",
        "m1_label": "System Status", "m1_val": "Online", "m1_delta": "Connection Ready",
        "m2_label": "Registered Cases", "m2_unit": "Patients",
        "m3_label": "Clinical Room", "m3_val": "Available", "m3_delta": "Ready for Session"
    }
}

# --- 1. BAĞLANTILAR ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. DİL SEÇİMİ VE TASARIM (Hata almamak için en üstte) ---
with st.sidebar:
    dil = st.radio("Language / Dil", options=["TR", "EN"], horizontal=True)
    L = LANG_DICT["tr"] if dil == "TR" else LANG_DICT["en"]

st.set_page_config(page_title=L["title"], page_icon="🧠", layout="wide")

# Dil değişirse sohbeti sıfırla
if "last_dil" not in st.session_state: st.session_state.last_dil = dil
if st.session_state.last_dil != dil:
    st.session_state.messages = []
    st.session_state.last_dil = dil
    st.rerun()

# --- 3. VERİTABANI VE KÜTÜPHANE ---
def vakalari_getir():
    try:
        response = supabase.table("vakalar").select("*").execute()
        kutuphane = {row["vaka_adi"]: {"kurallar": row["kurallar"], "ozet": row["ozet"]} for row in response.data}
        sec_key = "Seçiniz..." if dil == "TR" else "Select..."
        if sec_key not in kutuphane:
            kutuphane = {sec_key: {"kurallar": "...", "ozet": "..."}, **kutuphane}
        return kutuphane, sec_key
    except:
        return {"Seçiniz...": {"kurallar": "Hata", "ozet": "Hata"}}, "Seçiniz..."

vaka_kutuphanesi, sec_text = vakalari_getir()

def metni_sese_cevir(metin):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova", # 'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer' arasından seçebilirsin
            input=metin
        )
        # Sesi bellek üzerinde tutuyoruz (Dosya kaydetmeden hızlıca oynatmak için)
        audio_data = io.BytesIO(response.content)
        return audio_data
    except Exception as e:
        st.error(f"Ses oluşturma hatası: {e}")
        return None

# --- LOTTIE ANİMASYON YÜKLEYİCİ ---
def lottie_yukle(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()
lottie_dusunuyor = lottie_yukle("https://lottie.host/80d0d885-3b95-4eb8-a1e4-4ab23f990ea5/rYvT9j8XmO.json")

# --- 4. ANA EKRAN BANNER ---

# --- MODERN ARAYÜZ CSS ENJEKSİYONU ---
st.markdown("""
<style>
    /* Ana arka planı çok hafif bir gri yapıp kontrast sağlayalım */
    .stApp {
        background-color: #F8F9FA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Yan menü (Sidebar) stili - Daha yumuşak bir ton */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EAEAEA;
        box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Terapist (Kullanıcı) ve Danışan (AI) Sohbet Balonlarını Özelleştirme */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.04);
        margin-bottom: 15px;
        border: 1px solid #F0F0F0;
    }
    
    /* Metrikleri (Durum, Etkileşim) Apple/Modern UI tarzı kutulara alma */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.03);
        border-left: 4px solid #6C63FF; /* Tasarıma modern bir mor/lila dokunuşu */
    }
    
    /* Input (Yazı yazma) kutusunu yuvarlatma */
    .stChatInputContainer {
        border-radius: 20px !important;
        box-shadow: 0px 5px 15px rgba(0, 0, 0, 0.1) !important;
    }

    /* Expander (Hakkında / Bilgi Dosyası) kısımlarını yumuşatma */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div style='background: linear-gradient(to right, #2b5876, #4e4376); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px;'>
    <h1 style='color: white; margin: 0; font-size: 38px;'>{L['title']}</h1>
    <p style='color: #d1d1d1; font-size: 18px; font-style: italic;'>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR (HAKKINDA VE EKİP GERİ GELDİ) ---
with st.sidebar:
    st.title(L["title"])
    
    # PROJE HAKKINDA (Dinamik Uyarı Metni)
    with st.expander(L["expander_about"], expanded=False):
        if dil == "TR":
            st.markdown("""
            Bu platform, psikoloji öğrencilerinin klinik pratik yapması için geliştirilmiştir. 
            \nÖnemli Not: Bu uygulamada yer alan tüm vaka örnekleri ve karakterler tamamen kurgusal olup, 
            gerçek bir psikolojik danışmanlık hizmeti sunmamaktadır. Tanı ve tedavi süreçleri 
            yalnızca lisanslı ruh sağlığı profesyonelleri tarafından yürütülmelidir.
            """)
        else:
            st.markdown("""
            This platform is developed for psychology students to practice clinical skills. 
            \nImportant Note: All cases and characters are fictional and do not provide 
            real psychological counseling. Diagnosis and treatment processes should only 
            be conducted by licensed mental health professionals.
            """)

    st.divider()
    st.title(L["sidebar_title"])
    secilen_vaka_adi = st.selectbox(L["sidebar_title"], options=list(vaka_kutuphanesi.keys()), key="sim_vaka_sec")
    
    if st.button(L["reset_btn"]):
        st.session_state.messages = []
        st.rerun()

    # --- PROJE EKİBİ (LİNKEDIN BUTONLARI) ---
    st.sidebar.divider()
    ekip_baslik = "👨‍💻 Proje Ekibi" if dil == "TR" else "👨‍💻 Project Team"
    st.sidebar.subheader(ekip_baslik)
    
    # Emir Demir
    st.sidebar.info("**Emir Demir**\n" + ("Geliştirici - Yeni Medya ve YBS Öğrencisi" if dil == "TR" else "Developer - New Media and MIS Student"))
    # Ebru Demir
    st.sidebar.success("**Ebru Demir**\n" + ("Vaka Yazarı - Psikoloji Mezunu" if dil == "TR" else "Case Writer - Psychology Graduate "))
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.link_button("Emir Demir - LinkedIn", "https://www.linkedin.com/in/itsemirdemir/")
    with col2:
        st.link_button("Ebru Demir -  LinkedIn", "https://www.linkedin.com/in/ebru-demir-81a531369/")

# --- 6. SOHBET VE METRİKLER ---
if "mevcut_vaka" not in st.session_state: st.session_state.mevcut_vaka = secilen_vaka_adi
if st.session_state.mevcut_vaka != secilen_vaka_adi:
    st.session_state.messages = []
    st.session_state.mevcut_vaka = secilen_vaka_adi

vaka_verisi = vaka_kutuphanesi[secilen_vaka_adi]

if secilen_vaka_adi == sec_text:
    # --- METRİKLER VE KARŞILAMA ---
    st.info(L["welcome_msg"])
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(label=L["m1_label"], value=L["m1_val"], delta=L["m1_delta"])
    with c2: 
        kayitli_sayi = len([k for k in vaka_kutuphanesi.keys() if k != sec_text])
        st.metric(label=L["m2_label"], value=f"{kayitli_sayi} {L['m2_unit']}", delta="Live")
    with c3: st.metric(label=L["m3_label"], value=L["m3_val"], delta=L["m3_delta"])
else:
    # --- VAKA AKTİF ---
    st.subheader(f"🗣️ {secilen_vaka_adi}")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label="Status" if dil=="EN" else "Durum", value="Active")
    with col2: st.metric(label="Interaction" if dil=="EN" else "Etkileşim", value="Clinical")
    with col3: st.metric(label="Privacy" if dil=="EN" else "Gizlilik", value="Secure")

    with st.expander("📄 Info / Bilgi Dosyası"):
        st.write(vaka_verisi["ozet"])

    # GÜVENLİK KİLİDİ: Mesaj listesi yoksa KESİNLİKLE oluştur.
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if len(st.session_state.messages) == 0:
        # 1. DEĞİŞEN KISIM: ROLÜ KESİNLEŞTİREN SERT KOMUT (Selin Olmanı Engeller)
        if dil == "TR":
            dil_emri = "\nKATI KURAL: Sen DANIŞANSIN (Hasta). Karşındaki kişi TERAPİST. Asla terapist rolüne girme, sadece kendi derdini anlat ve sorulara cevap ver. Lütfen TÜRKÇE konuş."
        else:
            dil_emri = "\nSTRICT RULE: You are the PATIENT. The user is the THERAPIST. Never break character. Respond in ENGLISH."
        st.session_state.messages = [{"role": "system", "content": vaka_verisi["kurallar"] + dil_emri}]

    # Geçmiş mesajları ekrana çiz
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]): st.markdown(message["content"])

    # --- SESLİ GİRİŞ PANELİ ---
    st.divider()
    audio_data = mic_recorder(
        start_prompt="🎙️ Seansı Sesli Başlat" if dil == "TR" else "🎙️ Start Voice Session",
        stop_prompt="🛑 Durdur ve Gönder" if dil == "TR" else "🛑 Stop and Send",
        key="recorder"
    )

    prompt = None
    sesli_girdi_mi = False  # <--- İŞTE BÜYÜ TILSIMI BURADA BAŞLIYOR

    if audio_data and 'bytes' in audio_data:
        with st.spinner("Sesiniz anlaşılıyor..." if dil == "TR" else "Listening..."):
            audio_bio = io.BytesIO(audio_data['bytes'])
            audio_bio.name = "audio.webm" 
            
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_bio,
                    language="tr" 
                )
                
                gelen_metin = transcript.text.strip()
                yasakli_kelimeler = ["altyazı", "m.k", "m.k."]
                
                if gelen_metin and not any(yasak in gelen_metin.lower() for yasak in yasakli_kelimeler):
                    prompt = gelen_metin
                    sesli_girdi_mi = True  # <--- EĞER SES VARSA ANAHTARI AÇ!
                else:
                    st.warning("Sesiniz anlaşılamadı. Lütfen butona basıp 1 saniye bekledikten sonra konuşun.")
            except Exception as e:
                st.error(f"Whisper Hatası: {e}")
    else:
        prompt = st.chat_input(L["chat_placeholder"])
        # Burada sesli_girdi_mi zaten False olarak kalıyor.

    # --- SOHBETİ İŞLEME ---
    if prompt and prompt.strip() != "":
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Lottie animasyonunu göstermek için geçici bir alan açıyoruz
            animasyon_alani = st.empty()
            
            with animasyon_alani.container():
                if lottie_dusunuyor:
                    # Animasyon ortalanmış ve kibar bir boyutta
                    st_lottie(lottie_dusunuyor, height=60, key="typing_animation")
                else:
                    st.write("Düşünüyor..." if dil == "TR" else "Thinking...")

            try:
                # Arka planda AI cevabı üretiyor
                response = client.chat.completions.create(
                    model="gpt-5.4-nano", 
                    messages=st.session_state.messages,
                    temperature=0.4
                )
                answer = response.choices[0].message.content
                
                # AI cevabı hazır olunca animasyonu ekrandan siliyoruz!
                animasyon_alani.empty()
                
                # Ve gerçek cevabı ekrana basıyoruz
                st.markdown(answer)
                
                # --- AI SESLİ CEVAP ---
                if sesli_girdi_mi:
                    audio_file = metni_sese_cevir(answer)
                    if audio_file:
                        st.audio(audio_file, format="audio/mp3", autoplay=True)
                    
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                animasyon_alani.empty() # Hata olursa da animasyon takılı kalmasın
                st.error(f"Hata oluştu: {e}")