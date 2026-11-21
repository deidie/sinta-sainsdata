# Google Scholar lengkap: sinkronisasi dan verifikasi

## Mengapa hanya delapan artikel?
Snapshot sebelumnya mengambil endpoint Apps Script per dosen, dan kode `readPortal_()` membatasi artikel memakai `.slice(0,8)`. Angka 8 adalah batas tampilan API, **bukan** jumlah seluruh artikel di profil Google Scholar. `updateScholar()` lama juga meminta maksimal 100 artikel pertama tanpa pagination.

## Perbaikan yang tersedia di repo
- `sinkronisasi_scholar_lengkap.py`: ambil semua halaman Google Scholar Author API SerpApi (`num=100`, `start=0,100,200,...`), gabungkan, simpan semua artikel ke JSON.
- `test_scholar_lengkap.py`: uji pagination dan perlindungan terhadap pengurangan data tidak disengaja.
- `.github/workflows/sinkronisasi-scholar.yml`: jalankan tiap tanggal 1 pukul 08.22 WIB, atau manual.
- `hasil/publikasi_scholar.json`: sumber data untuk tampilan web. Snapshot lama telah ditandai `cakupan_lengkap=false`.

## Satu pengaturan yang harus dilakukan pemilik repo
GitHub tidak otomatis mewarisi `SERPAPI_KEY` dari Google Apps Script.

1. Buka **Apps Script → Project Settings → Script Properties** lalu lihat nilai `SERPAPI_KEY` yang memang digunakan oleh integrasi Scholar sebelumnya. Jangan bagikan kunci di chat atau berkas publik.
2. Buka repo GitHub **Settings → Secrets and variables → Actions → New repository secret**.
3. Isi **Name**: `SERPAPI_KEY`, dan **Secret**: nilai kunci dari Apps Script. Simpan.
4. Buka **Actions → Sinkronisasi Publikasi Google Scholar (Lengkap) → Run workflow**.
5. Setelah tindakan selesai dengan status **success**, buka `hasil/publikasi_scholar.json`. Pastikan `cakupan_lengkap=true` dan `jumlah_artikel_scholar` pada tiap dosen cocok dengan daftar `artikel_scholar`.

**Catatan:** Pengambilan semua halaman mengonsumsi kuota SerpApi berdasarkan jumlah halaman. Bila akun tidak memiliki kuota memadai, tugas gagal dan snapshot lama dipertahankan. Tidak ada API key yang dicantumkan dalam HTML atau JSON publik.

## Jika tidak menggunakan secret GitHub
Alternatifnya memperbarui dan menerbitkan ulang Apps Script agar endpoint publik mengirim seluruh baris sheet `Publikasi` tanpa `.slice(0,8)`, serta memperbarui `updateScholar()` untuk membaca halaman SerpApi selanjutnya. Tanpa perubahan itu, endpoint lama masih mengirim delapan artikel per dosen.

## Batas interpretasi data
- **Jumlah artikel Scholar** dihitung berdasarkan seluruh entri artikel profil yang berhasil ditarik setelah deduplikasi per dosen, bukan jumlah yang tersimpan di snapshot lama.
- **Sitasi Scholar** adalah nilai metrik masing-masing profil, bukan sitasi unik lintas dosen.
- **Publikasi tahunan** berasal dari tahun artikel, **bukan** grafik sitasi tahunan.
- **GARUDA, SINTA, dan Scopus** adalah sumber berbeda dan tidak boleh dianggap setara.
