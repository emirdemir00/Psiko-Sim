import streamlit as st
from openai import OpenAI
import time
import os
from supabase import create_client, Client 

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

# --- 4. ANA EKRAN BANNER ---
st.markdown(f"""
<div style='background: linear-gradient(to right, #2b5876, #4e4376); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px;'>
    <h1 style='color: white; margin: 0; font-size: 38px;'>{L['title']}</h1>
    <p style='color: #d1d1d1; font-size: 18px; font-style: italic;'>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR (PANEL VE EKİP) ---
with st.sidebar:
    st.title(L["title"])
    with st.expander(L["expander_about"]):
        st.write("Psikoloji simülasyon platformu.")
    
    st.divider()
    st.title(L["sidebar_title"])
    secilen_vaka_adi = st.selectbox(L["sidebar_title"], options=list(vaka_kutuphanesi.keys()), key="sim_vaka_sec")
    
    if st.button(L["reset_btn"]):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.sidebar.info("**Emir Demir**\nDeveloper")

# --- 6. SOHBET VE METRİKLER ---
if "mevcut_vaka" not in st.session_state: st.session_state.mevcut_vaka = secilen_vaka_adi
if st.session_state.mevcut_vaka != secilen_vaka_adi:
    st.session_state.messages = []
    st.session_state.mevcut_vaka = secilen_vaka_adi

vaka_verisi = vaka_kutuphanesi[secilen_vaka_adi]

if secilen_vaka_adi == sec_text:
    # --- METRİKLER GERİ GELDİ ---
    st.info(L["welcome_msg"])
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(label=L["m1_label"], value=L["m1_val"], delta=L["m1_delta"])
    with c2: 
        kayitli_sayi = len([k for k in vaka_kutuphanesi.keys() if k != sec_text])
        st.metric(label=L["m2_label"], value=f"{kayitli_sayi} {L['m2_unit']}", delta="Live")
    with c3: st.metric(label=L["m3_label"], value=L["m3_val"], delta=L["m3_delta"])
else:
    # Vaka Aktifken Görünecek Metrikler
    st.subheader(f"🗣️ {secilen_vaka_adi}")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label="Status" if dil=="EN" else "Durum", value="Active")
    with col2: st.metric(label="Interaction" if dil=="EN" else "Etkileşim", value="Clinical")
    with col3: st.metric(label="Privacy" if dil=="EN" else "Gizlilik", value="Secure")

    with st.expander("📄 Info / Bilgi Dosyası"):
        st.write(vaka_verisi["ozet"])

    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        dil_emri = "\nLütfen TÜRKÇE konuş." if dil == "TR" else "\nPlease respond in ENGLISH."
        st.session_state.messages = [{"role": "system", "content": vaka_verisi["kurallar"] + dil_emri}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input(L["chat_placeholder"]):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = client.chat.completions.create(model="gpt-4o", messages=st.session_state.messages, temperature=0.4)
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})