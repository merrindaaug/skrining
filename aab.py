import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# 1. Konfigurasi Halaman & Judul
st.set_page_config(page_title="Riset Kesehatan Mental", page_icon="🧠")

st.title("🧠 AI Deteksi Dini Kesehatan Mental")
st.caption("Instrumen: Self Reporting Questionnaire (SRQ-20)")

# 2. Sidebar untuk Data Identitas
with st.sidebar:
    st.header("Informasi Responden")
    res_id = st.text_input("ID Responden / Nama Inisial", placeholder="Contoh: R001")
    consent = st.checkbox("Saya bersedia mengikuti skrining ini.")
    
    st.divider()
    st.info("SRQ-20 dikembangkan oleh WHO untuk skrining gangguan jiwa di pelayanan kesehatan primer.")

# 3. List Pertanyaan (SRQ-20)
questions = [
    "Apakah Anda sering menderita sakit kepala?", "Apakah Anda tidak nafsu makan?", 
    "Apakah Anda sulit tidur?", "Apakah Anda mudah merasa takut?",
    "Apakah Anda merasa tegang, cemas, atau kuatir?", "Apakah tangan Anda gemetar?",
    "Apakah pencernaan Anda terganggu/buruk?", "Apakah Anda sulit untuk berpikir jernih?",
    "Apakah Anda merasa tidak bahagia?", "Apakah Anda menangis lebih sering?",
    "Apakah Anda merasa sulit untuk menikmati aktivitas sehari-hari?", "Apakah Anda sulit untuk mengambil keputusan?",
    "Apakah pekerjaan Anda sehari-hari terganggu?", "Apakah Anda tidak mampu melakukan hal-hal yang bermanfaat dalam hidup?",
    "Apakah Anda kehilangan minat pada berbagai hal?", "Apakah Anda merasa tidak berharga?",
    "Apakah Anda mempunyai pikiran untuk mengakhiri hidup?", "Apakah Anda merasa lelah sepanjang waktu?",
    "Apakah Anda merasa tidak enak di perut?", "Apakah Anda mudah lelah?"
]

# 4. Form Kuesioner
with st.form("srq_form"):
    st.write("Jawablah pertanyaan berikut sesuai kondisi Anda dalam **30 hari terakhir**.")
    user_responses = []
    
    for i, q in enumerate(questions):
        choice = st.radio(f"{i+1}. {q}", options=["Tidak", "Ya"], horizontal=True, key=f"q{i}")
        user_responses.append(1 if choice == "Ya" else 0)
    
    submit_btn = st.form_submit_button("Analisis & Simpan Data")

# 5. Logika Simpan Data & Hasil
if submit_btn:
    if not res_id or not consent:
        st.warning("⚠️ Mohon isi ID Responden dan centang persetujuan di sidebar.")
    else:
        total_score = sum(user_responses)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Susun baris data baru
        row_data = {
            "Timestamp": timestamp,
            "ID_Responden": res_id,
            "Total_Skor": total_score,
            "Status": "Indikasi Gangguan" if total_score >= 6 else "Normal"
        }
        # Masukkan detail jawaban Q1-Q20
        for i, val in enumerate(user_responses):
            row_data[f"Q{i+1}"] = val
        
        new_entry = pd.DataFrame([row_data])
        
        try:
            # Koneksi ke GSheets
            conn = st.connection("gsheets", type=GSheetsConnection)
            
            # Membaca data yang sudah ada (gunakan nama worksheet yang sesuai, misal: Sheet1)
            # ttl=0 memastikan data selalu fresh
            try:
                existing_data = conn.read(worksheet="Sheet1", ttl=0)
                existing_data = existing_data.dropna(how="all")
            except:
                existing_data = pd.DataFrame() # Jika sheet masih kosong
            
            # Gabungkan data
            updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
            
            # Update ke Google Sheets
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.success("✅ Data berhasil tersimpan di database riset.")
            
            # Tampilkan Hasil ke User
            st.divider()
            st.metric("Skor Anda", f"{total_score} / 20")
            if total_score >= 6:
                st.error("Hasil skrining menunjukkan indikasi gangguan mental emosional. Disarankan konsultasi ke profesional.")
            else:
                st.success("Kondisi Anda dalam batas normal. Tetap jaga kesehatan mental!")
            
            if user_responses[16] == 1:
                st.warning("⚠️ **Peringatan Penting:** Jawaban Anda menunjukkan adanya pikiran untuk menyakiti diri sendiri. Harap segera hubungi layanan kesehatan jiwa atau orang terpercaya.")
                
        except Exception as e:
            st.error(f"Gagal menyambung ke database. Pastikan konfigurasi Secrets sudah benar.")
            # Tombol cadangan jika koneksi internet/GSheets gagal
            st.download_button(
                label="Unduh Data Anda (CSV)", 
                data=new_entry.to_csv(index=False).encode('utf-8'), 
                file_name=f"hasil_{res_id}.csv",
                mime="text/csv"
            )
