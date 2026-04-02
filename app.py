import streamlit as st
from openai import OpenAI
import time
import json
import os

# 1. api anahtarı
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- hafıza ---
DOSYA_ADI = "vakalar.json"

def veritabani_olustur():
    varsayilan_veriler = {
        "Seçiniz...": {
            "kurallar": "Lütfen yan menüden bir vaka seçerek simülasyonu başlatın.",
            "ozet": "Henüz bir danışan seçilmedi."
        }
    }
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(varsayilan_veriler, f, ensure_ascii=False, indent=4)

def vakalari_getir():
    if not os.path.exists(DOSYA_ADI):
        veritabani_olustur()
    with open(DOSYA_ADI, "r", encoding="utf-8") as f:
        return json.load(f)

def vakalari_kaydet(veriler):
    with open(DOSYA_ADI, "w", encoding="utf-8") as f:
        json.dump(veriler, f, ensure_ascii=False, indent=4)

vaka_kutuphanesi = vakalari_getir()

# ---------------------------------------------

# 2. tasarım
st.set_page_config(page_title="Psiko-Sim Laboratuvarı", page_icon="🧠", layout="wide")

# --- üst ve yan boşlukları kapat ---
st.markdown("""
    <style>
            .block-container {
                padding-top: 1.5rem;   /* Üst boşluğu ayarlar */
                padding-left: 1rem;    /* SOL boşluğu tıraşlar */
                padding-right: 1rem;   /* SAĞ boşluğu tıraşlar */
            }
    </style>
    """, unsafe_allow_html=True)

# ------------------------------------
# 3. YAN MENÜ (SIDEBAR) - İLETİŞİM VE HAKKINDA EKLEDİM
with st.sidebar:
    st.title("🧠 Psiko-Sim Lab")
    
    # --- PROJE HAKKINDA KISMI ---
    with st.expander("ℹ️ Proje Hakkında", expanded=False):
        st.markdown("""
        Bu platform, psikoloji öğrencilerinin klinik pratik yapması için geliştirilmiştir.
        
        **Özellikler:**
        - AI Tabanlı Danışanlar
        - Dinamik Vaka Yönetimi
        - Otomatik Klinik Raporlama
        """)

    st.divider()
    st.title("🗂 Danışan Kütüphanesi")
    
    with st.expander("🛠️ Yetkili Paneli (Gizli)"):
        girilen_sifre = st.text_input("Uzman Şifresi:", type="password")
        
        if girilen_sifre == "nisanyagmuru":
            st.success("Kilit açıldı. Hoş geldiniz!")
            
            tab1, tab2, tab3 = st.tabs(["➕ Ekle", "🗑️ Sil", "✏️ Düzenle"])
            
            with tab1:
                yeni_vaka_adi = st.text_input("Danışan Adı (Örn: Ayşe - Panik Atak)")
                yeni_vaka_detayi = st.text_area("Vaka Senaryosu ve AI Kuralları", height=150, key="yeni_vaka_ekle")
                
                if st.button("Vakayı Sisteme Ekle"):
                    if yeni_vaka_adi and yeni_vaka_detayi:
                        klinik_ozet = ""
                        try:
                            sistem_istemi = f"Lütfen aşağıdaki metinden sadece hastanın demografik bilgilerini ve klinik durumunu anlatan 2-3 cümlelik profesyonel bir klinik ön rapor çıkar:\n\n{yeni_vaka_detayi}"
                            response = client.chat.completions.create(
                                model="gpt-5.4-nano",
                                messages=[{"role": "user", "content": sistem_istemi}],
                                temperature=0.3
                            )
                            klinik_ozet = response.choices[0].message.content
                        except Exception as e:
                            klinik_ozet = "Özet oluşturulamadı (API bağlantısı bekleniyor)."

                        vaka_kutuphanesi[yeni_vaka_adi] = {
                            "kurallar": yeni_vaka_detayi,
                            "ozet": klinik_ozet
                        }
                        vakalari_kaydet(vaka_kutuphanesi) 
                        st.success(f"✅ {yeni_vaka_adi} eklendi.")
                        time.sleep(1.5)
                        st.rerun()

            with tab2:
                silinecek_vaka = st.selectbox(
                    "Silinecek Vaka:", 
                    options=[v for v in vaka_kutuphanesi.keys() if v != "Seçiniz..."],
                    key="sil_selectbox"
                )
                if st.button("Seçili Vakayı Kalıcı Olarak Sil", type="primary"):
                    if silinecek_vaka:
                        del vaka_kutuphanesi[silinecek_vaka]
                        vakalari_kaydet(vaka_kutuphanesi) 
                        st.error(f"🗑️ {silinecek_vaka} silindi.")
                        time.sleep(1.5)
                        st.rerun()

            with tab3:
                duzenlenecek_ad = st.selectbox(
                    "Düzenlenecek Vaka:", 
                    options=[v for v in vaka_kutuphanesi.keys() if v != "Seçiniz..."],
                    key="duzenle_selectbox"
                )
                if duzenlenecek_ad:
                    eski_kurallar = vaka_kutuphanesi[duzenlenecek_ad]["kurallar"]
                    yeni_kurallar = st.text_area("Senaryoyu Güncelle:", value=eski_kurallar, height=200, key="duzenle_area")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Sadece Metni Kaydet"):
                            vaka_kutuphanesi[duzenlenecek_ad]["kurallar"] = yeni_kurallar
                            vakalari_kaydet(vaka_kutuphanesi)
                            st.success("Güncellendi!")
                            time.sleep(1)
                            st.rerun()
                    with c2:
                        if st.button("Metni Kaydet ve Özeti Yenile"):
                            with st.spinner("Yapay zeka yeni özeti yazıyor..."):
                                try:
                                    sistem_istemi = f"Lütfen aşağıdaki klinik durumdan profesyonel bir özet çıkar:\n\n{yeni_kurallar}"
                                    response = client.chat.completions.create(
                                        model="gpt-5.4-nano",
                                        messages=[{"role": "user", "content": sistem_istemi}],
                                        temperature=0.3
                                    )
                                    yeni_ozet = response.choices[0].message.content
                                    vaka_kutuphanesi[duzenlenecek_ad]["kurallar"] = yeni_kurallar
                                    vaka_kutuphanesi[duzenlenecek_ad]["ozet"] = yeni_ozet
                                    vakalari_kaydet(vaka_kutuphanesi)
                                    st.success("Vaka ve Özet güncellendi!")
                                    time.sleep(1)
                                    st.rerun()
                                except:
                                    st.error("API hatası!")
                    
        elif girilen_sifre != "":
            st.error("Hatalı şifre!")
            
    st.divider()
    secilen_vaka_adi = st.selectbox("Simüle edilecek danışan:", options=list(vaka_kutuphanesi.keys()))
    
    st.divider()
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

    # --- GELİŞTİRİCİ & DANIŞMAN KISMI ---
    st.sidebar.divider()
    st.sidebar.subheader("👨‍💻 Proje Ekibi")
    
    # Senin Bilgilerin
    st.sidebar.info("**Emir Demir**\nGeliştirici - nYeni Medya ve Yönetim Bİlişim Sistemleri Öğrencisi")
    
    # Ablanın Bilgileri
    st.sidebar.success("**Ebru Demir**\nVaka Yazarı - Psikoloji Mezunu")
    
    # İletişim & Linkler
    st.sidebar.write("🔗 **Bağlantılar:**")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.link_button("Emir Demir LinkedIn", "https://www.linkedin.com/in/itsemirdemir/")
    with col2:
        st.link_button("Ebru Demir LinkedIn", "https://www.linkedin.com/in/ebru-demir-81a531369/")

    st.sidebar.caption("📧 itsemirdemir@gmail.com")
# 4. hafıza temizliği
if "mevcut_vaka" not in st.session_state:
    st.session_state.mevcut_vaka = secilen_vaka_adi

if st.session_state.mevcut_vaka != secilen_vaka_adi:
    st.session_state.messages = [] 
    st.session_state.mevcut_vaka = secilen_vaka_adi

secilen_vaka_verisi = vaka_kutuphanesi[secilen_vaka_adi]
vaka_kurallar = secilen_vaka_verisi["kurallar"] if isinstance(secilen_vaka_verisi, dict) else secilen_vaka_verisi
vaka_ozet = secilen_vaka_verisi["ozet"] if isinstance(secilen_vaka_verisi, dict) else secilen_vaka_verisi

# 5. ana ekran
st.markdown("""
<div style='background: linear-gradient(to right, #2b5876, #4e4376); padding: 20px; border-radius: 10px; text-align: center; color: white; margin-bottom: 25px;'>
    <h1 style='color: white; margin: 0; font-size: 36px;'>🧠 Psiko-Sim Laboratuvarı</h1>
    <p style='margin: 5px 0 0 0; font-size: 18px; opacity: 0.9;'>Psikolog Adayları İçin Sanal Danışanlar</p>
</div>
""", unsafe_allow_html=True)

if secilen_vaka_adi == "Seçiniz...":
    st.info("👈 Seansa başlamak için sol menüden bir danışan dosyası seçin.")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric(label="Sistem Durumu", value="Çevrimiçi")
    with c2: st.metric(label="Kayıtlı Vaka", value=len(vaka_kutuphanesi)-1)
    with c3: st.metric(label="Klinik Oda", value="Müsait")
else:
    st.subheader(f"🗣 Danışan: {secilen_vaka_adi}")
    with st.expander("📄 Danışan Klinik Ön Bilgi Dosyası"):
        st.info("Bu bilgiler seans öncesi terapiste verilen ön rapordur.")
        st.write(vaka_ozet)

    st.divider()

    # 6. sohbet hafızası
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = [{"role": "system", "content": vaka_kurallar}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 7. sohbet girişi
    if prompt := st.chat_input("Terapist olarak sorunuzu yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="gpt-5.4-nano",
                    messages=st.session_state.messages,
                    temperature=0.4
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error("Cevap üretilemiyor, lütfen API bağlantısını kontrol edin.")