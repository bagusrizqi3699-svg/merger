# Video Merger — build portable Windows EXE

Paket ini membangun GUI `VIDEO_MERGER.py` menjadi aplikasi Windows dan menyertakan FFmpeg.
PC target tidak perlu memasang Python atau FFmpeg secara terpisah.

## Cara mendapatkan EXE tanpa memasang Python di laptop sendiri

1. Buat repository baru di GitHub (private boleh).
2. Upload semua isi folder paket ini ke repository, termasuk folder `.github/workflows`.
3. Buka tab **Actions** pada repository.
4. Pilih workflow **Build Windows EXE**, lalu klik **Run workflow**.
5. Setelah selesai berstatus hijau, buka run tersebut dan unduh artifact `VideoMerger-Windows-Portable`.
6. Ekstrak ZIP. Jalankan `VideoMerger.exe` dari folder `VideoMerger` yang sudah diekstrak.

## Penting
- Jangan pisahkan `VideoMerger.exe`, `ffmpeg.exe`, DLL, dan folder `_internal`.
- FFmpeg essentials didownload saat build dari gyan.dev.
- NVENC tergantung GPU NVIDIA yang kompatibel serta driver yang terpasang.
- Uji dengan beberapa pasangan klip terlebih dahulu. Kode asal mengambil audio dari video depan.
