import streamlit as st
from openai import OpenAI
import time
import os
from supabase import create_client, Client # Yeni kütüphane eklendi

# --- 1. BAĞLANTILAR (Secrets'tan çekiliyor) ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Supabase Bağlantısı
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- 2. BULUT VERİTABANI FONKSİYONLARI (JSON YERİNE) ---

def vakalari_getir():
    try:
        # Supabase 'vakalar' tablosundaki her şeyi çek
        response = supabase.table("vakalar").select("*").execute()
        # Eğer tablo tamamen boşsa varsayılanı döndür
        if not response.data:
            return {"Seçiniz...": {"kurallar": "Lütfen yan menüden bir vaka seçin.", "ozet": "Henüz bir danışan seçilmedi."}}
        
        # Veriyi sözlük formatına çevir
        kutuphane = {row["vaka_adi"]: {"kurallar": row["kurallar"], "ozet": row["ozet"]} for row in response.data}
        
        # "Seçiniz..." her zaman en başta olsun
        if "Seçiniz..." not in kutuphane:
            kutuphane = {"Seçiniz...": {"kurallar": "Lütfen yan menüden bir vaka seçin.", "ozet": "Henüz bir danışan seçilmedi."}, **kutuphane}
        return kutuphane
    except Exception as e:
        return {"Seçiniz...": {"kurallar": f"Hata: {e}", "ozet": "Veritabanı bağlantısı kurulamadı."}}

def vaka_kaydet_bulut(ad, kurallar, ozet):
    # Upsert: Vaka varsa günceller, yoksa yeni satır açar
    supabase.table("vakalar").upsert({
        "vaka_adi": ad, 
        "kurallar": kurallar, 
        "ozet": ozet
    }).execute()

def vaka_sil_bulut(ad):
    # Tablodan vaka adına göre siler
    supabase.table("vakalar").delete().eq("vaka_adi", ad).execute()

# Kütüphaneyi buluttan çek
vaka_kutuphanesi = vakalari_getir()

# ---------------------------------------------)

# ANA EKRAN (BANNER VE AÇIKLAMA)
st.markdown("""
<div style='background: linear-gradient(to right, #2b5876, #4e4376); padding: 25px; border-radius: 12px; text-align: center; color: white; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
    <h1 style='color: white; margin: 0; font-size: 38px; font-weight: bold;'>🧠 Psiko-Sim Laboratuvarı</h1>
    <p style='color: #d1d1d1; font-size: 18px; margin-top: 10px; font-style: italic;'>Psikolog adayları için geliştirilmiş sanal danışan simülasyonu</p>
</div>
""", unsafe_allow_html=True)
# ------------------------------------
# 4. YAN MENÜ (SIDEBAR)
with st.sidebar:
    st.title("🧠 Psiko-Sim Lab")
    
    with st.expander("ℹ️ Proje Hakkında", expanded=False):
        st.markdown("""
        Bu platform, psikoloji öğrencilerinin klinik pratik yapması için geliştirilmiştir. Önemli Not: Bu uygulamada yer alan tüm vaka örnekleri ve karakterler tamamen kurgusal olup, herhangi bir gerçek kişiyle benzerlik göstermesi tesadüfidir. Vaka içerikleri; psikoloji öğrencileri, uzmanlar ve ilgili alanlarda eğitim alan bireyler için eğitim ve simülasyon amacıyla hazırlanmıştır. Bu uygulama, gerçek bir psikolojik danışmanlık veya terapi hizmeti sunmamaktadır ve bu amaçla kullanılmamalıdır. Uygulama içerisinde gerçekleştirilen simülasyonlar, terapötik sürecin birebir karşılığı olmayıp, yalnızca olası senaryolar üzerinden beceri geliştirmeyi desteklemeyi hedeflemektedir. Her bireyin yaşantısı, psikolojik yapısı ve terapi sürecine verdiği tepkiler farklıdır. Bu nedenle, burada sunulan vakalar ve olası müdahale yolları genellenebilir veya kesin doğrular olarak değerlendirilmemelidir. Uygulama içeriği, kullanıcıların klinik karar verme süreçlerinin yerini almaz. Tanı koyma, müdahale planlama ve tedavi süreçleri yalnızca yetkin ve lisanslı ruh sağlığı profesyonelleri tarafından yürütülmelidir. Eğer siz veya çevrenizdeki biri psikolojik destek ihtiyacı içindeyse, lütfen bir uzman psikolog, psikiyatrist veya ilgili sağlık profesyoneline başvurunuz. Uygulamanın kullanımından doğabilecek doğrudan veya dolaylı sonuçlardan geliştirici ekip sorumlu tutulamaz.
        """)

    st.divider()
    st.title("🗂 Danışan Kütüphanesi")
    
    with st.expander("🛠️ Yetkili Paneli (Gizli)"):
        girilen_sifre = st.text_input("Uzman Şifresi:", type="password")
        
        if girilen_sifre == "nisanyagmuru":
            st.success("Kilit açıldı.")
            
            tab1, tab2, tab3 = st.tabs(["➕ Ekle", "🗑️ Sil", "✏️ Düzenle"])
            
            with tab1:
                yeni_vaka_adi = st.text_input("Danışan Adı (Örn: Ayşe - Panik Atak)")
                yeni_vaka_detayi = st.text_area("Vaka Senaryosu ve AI Kuralları", height=150, key="yeni_vaka_ekle")
                
                if st.button("Vakayı Sisteme Ekle"):
                    if yeni_vaka_adi and yeni_vaka_detayi:
                        with st.spinner("Vaka oluşturuluyor..."):
                            try:
                                sistem_istemi = f"Lütfen aşağıdaki metinden sadece danışanın adını, meslek bilgisini ve başvuru nedenini çıkar, 'hasta' kelimesini kullanma:\n\n{yeni_vaka_detayi}"
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[{"role": "user", "content": sistem_istemi}],
                                    temperature=0.3
                                )
                                klinik_ozet = response.choices[0].message.content
                            except:
                                klinik_ozet = "Özet oluşturulamadı."

                            # BULUTA KAYDET
                            vaka_kaydet_bulut(yeni_vaka_adi, yeni_vaka_detayi, klinik_ozet)
                            st.success(f"✅ {yeni_vaka_adi} buluta kaydedildi.")
                            time.sleep(1)
                            st.rerun()

            with tab2:
                silinecek_vaka = st.selectbox(
                    "Silinecek Vaka:", 
                    options=[v for v in vaka_kutuphanesi.keys() if v != "Seçiniz..."],
                    key="sil_selectbox"
                )
                if st.button("Seçili Vakayı Kalıcı Olarak Sil", type="primary"):
                    if silinecek_vaka:
                        vaka_sil_bulut(silinecek_vaka) # BULUTTAN SİL
                        st.error(f"🗑️ {silinecek_vaka} silindi.")
                        time.sleep(1)
                        st.rerun()

            with tab3:
                duzenlenecek_ad = st.selectbox(
                    "Düzenlenecek Vaka:", 
                    options=[v for v in vaka_kutuphanesi.keys() if v != "Seçiniz..."],
                    key="duzenle_vaka_secimi"
                )
                if duzenlenecek_ad:
                    eski_kurallar = vaka_kutuphanesi[duzenlenecek_ad]["kurallar"]
                    yeni_kurallar = st.text_area("Senaryoyu Güncelle:", value=eski_kurallar, height=200, key=f"area_{duzenlenecek_ad}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Sadece Metni Kaydet"):
                            vaka_kaydet_bulut(duzenlenecek_ad, yeni_kurallar, vaka_kutuphanesi[duzenlenecek_ad]["ozet"])
                            st.success("Güncellendi!")
                            st.rerun()
                    with c2:
                        if st.button("Metni Kaydet ve Özeti Yenile"):
                            with st.spinner("Yenileniyor..."):
                                try:
                                    sistem_istemi = f"Aşağıdaki klinik vakanın sadece adını, meslek bilgisini ve başvuru nedenini çıkar...\n\n{yeni_kurallar}"
                                    response = client.chat.completions.create(
                                        model="gpt-4o",
                                        messages=[{"role": "user", "content": sistem_istemi}],
                                        temperature=0.3
                                    )
                                    yeni_ozet = response.choices[0].message.content
                                    vaka_kaydet_bulut(duzenlenecek_ad, yeni_kurallar, yeni_ozet)
                                    st.success("Bulut Güncellendi!")
                                    st.rerun()
                                except:
                                    st.error("Hata!")

    st.divider()
    secilen_vaka_adi = st.selectbox("Simüle edilecek danışan:", options=list(vaka_kutuphanesi.keys()), key="sim_vaka_sec")
    
    if st.button("Sohbeti Sıfırla"):
        st.session_state.messages = []
        st.rerun()

    # --- EKİP & LİNK BUTONLARI ---
    st.sidebar.divider()
    st.sidebar.subheader("👨‍💻 Proje Ekibi")
    st.sidebar.info("**Emir Demir**\nGeliştirici - Yeni Medya Öğrencisi")
    st.sidebar.success("**Ebru Demir**\nVaka Yazarı - Psikoloji Mezunu")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.link_button("Emir LinkedIn", "https://www.linkedin.com/in/itsemirdemir/")
    with col2:
        st.link_button("Ebru LinkedIn", "https://www.linkedin.com/in/ebru-demir-81a531369/")

# 5. SOHBET MANTIĞI
if "mevcut_vaka" not in st.session_state:
    st.session_state.mevcut_vaka = secilen_vaka_adi

if st.session_state.mevcut_vaka != secilen_vaka_adi:
    st.session_state.messages = [] 
    st.session_state.mevcut_vaka = secilen_vaka_adi

secilen_vaka_verisi = vaka_kutuphanesi[secilen_vaka_adi]
vaka_kurallar = secilen_vaka_verisi["kurallar"]
vaka_ozet = secilen_vaka_verisi["ozet"]

if secilen_vaka_adi == "Seçiniz...":
    st.info("👈 Seansa başlamak için sol menüden bir danışan dosyası seçin.")
else:
    st.subheader(f"🗣 Danışan: {secilen_vaka_adi}")
    with st.expander("📄 Danışan Klinik Ön Bilgi Dosyası"):
        st.write(vaka_ozet)

    st.divider()

    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = [{"role": "system", "content": vaka_kurallar}]

    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("Terapist olarak sorunuzu yazın..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages,
                    temperature=0.4
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except:
                st.error("Cevap üretilemiyor.")