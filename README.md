### Kalkulator Daya Dukung Tiang (Sederhana) – Python

**Satuan**: kPa, m, kN

#### Cara Menjalankan

```bash
python pile_capacity.py
```

Ikuti pertanyaan di layar. Anda dapat memilih menghitung luas ujung dan keliling dari diameter, atau memasukkan langsung `Ab` dan keliling.

#### Antarmuka (UI) Streamlit

Instal dependensi:

```bash
pip install -r requirements.txt
```

Jalankan UI:

```bash
streamlit run app.py
```

Struktur modul:
- `axpile/models.py` — tipe data `SoilLayer`, validasi input.
- `axpile/geometry.py` — fungsi geometri (luas ujung, keliling).
- `axpile/calc.py` — ekspansi lapisan sampai kedalaman, perhitungan Qfs, Qb, Qult, Qall vs depth.
- `axpile/plots.py` — helper grafik Plotly.
- `app.py` — UI Streamlit yang menggunakan modul-modul di atas.

Input:
- Diameter tiang (m), Kedalaman tiang (m), FS
- Daftar lapisan tanah (urut dari atas):
  - Pilih jenis tanah: clay atau sand
  - Clay: Su (kPa), alpha, Nc
  - Sand: gamma' (kN/m³), beta, Nq

Output:
- Rekapan Ab, perimeter, Qb, Qfs, Qult, Qall
- Grafik Depth vs Qall
- Grafik Depth vs (Qfs, Qb, Qult, Qall)

#### Input yang Diminta
- **Diameter tiang (m)** atau langsung: **Ab (m^2)** dan **keliling (m)**
- **qb (kPa)**: kuat dukung ujung di dasar tiang
- Daftar lapisan tanah sepanjang selimut tiang:
  - **tebal lapisan (m)**
  - **qs (kPa)**: gesekan selimut rata-rata untuk lapisan tersebut
- **FS**: faktor keamanan

Masukkan `0` pada tebal lapisan untuk mengakhiri input lapisan.

#### Perhitungan
- `Qb = qb * Ab`
- `Qs = sum(qs_i * perimeter * tebal_i)`
- `Qult = Qb + Qs`
- `Qa = Qult / FS`

#### Catatan dan Asumsi
- Kalkulator ini sederhana dan mengharuskan pengguna menyediakan nilai `qb` dan `qs` yang sesuai dari investigasi tanah atau pedoman desain.
- Pastikan konsistensi satuan: kPa untuk tegangan, m untuk panjang, kN untuk gaya.



