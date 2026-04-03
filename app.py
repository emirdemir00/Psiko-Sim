import streamlit as st
from openai import OpenAI
import time
import os
from supabase import create_client, Client 

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
        "reset_btn": "Sohbeti Sıfırla"
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
        "reset_btn": "Reset Chat"
    }
}

# --- 1. BAĞLANTILAR ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. DİL SEÇİMİ (Hata almamak için en üste aldık) ---
with st.sidebar:
    dil = st.radio("Language / Dil", options=["TR", "EN"], horizontal=True)
    L = LANG_DICT["tr"] if dil == "TR" else LANG_DICT["en"]

# --- 3. TASARIM AYARLARI ---
st.set_page_config(page_title=L["title"], page_icon="🧠", layout="wide")

# Dil değişirse sohbeti sıfırla
if "last_dil" not in st.session_state:
    st.session_state.last_dil = dil

if st.session_state.last_dil != dil:
    st.session_state.messages = []
    st.session_state.last_dil = dil
    st.rerun()

# --- 4. VERİTABANI FONKSİYONLARI ---
def vakalari_getir():
    try:
        response = supabase.table("vakalar").select("*").execute()
        if not response.data:
            return {"Seçiniz...": {"kurallar": "Lütfen vaka seçin.", "ozet": "Seçilmedi."}}
        kutuphane = {row["vaka_adi"]: {"kurallar": row["kurallar"], "ozet": row["ozet"]} for row in response.data}
        if "Seçiniz..." not in kutuphane:
            kutuphane = {"Seçiniz...": {"kurallar": "Seçin.", "ozet": "Seçilmedi."}, **kutuphane}
        return kutuphane
    except:
        return {"Seçiniz...": {"kurallar": "Hata", "ozet": "Hata"}}

vaka_kutuphanesi = vakalari_getir()

# --- 5. ANA EKRAN BAŞLIK ---
st.markdown(f"""
<div style='background: linear-gradient(to right, #2b5876, #4e4376); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px;'>
    <h1 style='color: white; margin: 0;'>{L['title']}</h1>
    <p style='color: #d1d1d1; margin-top: 10px;'>{L['subtitle']}</p>
</div>
""", unsafe_allow_html=True)

# --- 6. YAN MENÜ VE YETKİLİ PANELİ ---
with st.sidebar:
    st.title(L["title"])
    with st.expander(L["expander_about"]):
        st.write("Proje detayları buraya...") # Burayı L["about_text"] gibi bir yere bağlayabilirsin.

    st.divider()
    st.title(L["sidebar_title"])
    
    with st.expander(L["expander_admin"]):
        girilen_sifre = st.text_input(L["auth_label"], type="password")
        if st.button(L["login_btn"]):
            if girilen_sifre == "nisanyagmuru":
                st.success("Admin OK")
            else:
                st.error("Error")

    secilen_vaka_adi = st.selectbox(L["sidebar_title"], options=list(vaka_kutuphanesi.keys()), key="sim_vaka_sec")
    if st.button(L["reset_btn"]):
        st.session_state.messages = []
        st.rerun()

# --- 7. SOHBET MANTIĞI ---
if "mevcut_vaka" not in st.session_state:
    st.session_state.mevcut_vaka = secilen_vaka_adi

if st.session_state.mevcut_vaka != secilen_vaka_adi:
    st.session_state.messages = [] 
    st.session_state.mevcut_vaka = secilen_vaka_adi

vaka_verisi = vaka_kutuphanesi[secilen_vaka_adi]

if secilen_vaka_adi != "Seçiniz...":
    st.subheader(f"🗣️ {secilen_vaka_adi}")
    with st.expander("📄 Info / Özet"):
        st.write(vaka_verisi["ozet"])

    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        # AI'ya verilen gizli dil emri!
        dil_emri = "\nLütfen sadece TÜRKÇE konuş." if dil == "TR" else "\nIMPORTANT: Please respond ONLY in ENGLISH. Act as the patient."
        st.session_state.messages = [{"role": "system", "content": vaka_verisi["kurallar"] + dil_emri}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input(L["chat_placeholder"]):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = client.chat.completions.create(
                model="gpt-4o", # gpt-5.4-nano henüz yok, stabilite için 4o öneririm kral
                messages=st.session_state.messages,
                temperature=0.4
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})