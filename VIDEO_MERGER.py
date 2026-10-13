import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import os
import glob
import sys

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BG        = "#0d0f14"
PANEL     = "#161a22"
ACCENT    = "#00b4d8"
ACCENT2   = "#0077b6"
TEXT      = "#e0e6f0"
SUBTEXT   = "#6b7a99"
SUCCESS   = "#00c896"
WARNING   = "#f4a261"
DANGER    = "#e63946"
GPU_COLOR = "#9b5de5"
FONT_HEAD = ("Courier New", 13, "bold")
FONT_BODY = ("Courier New", 10)
FONT_LOG  = ("Courier New", 9)


# Locate bundled FFmpeg when packaged; otherwise use FFmpeg from PATH.
def ffmpeg_executable():
    app_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    bundled = os.path.join(app_dir, "ffmpeg.exe")
    return bundled if os.path.isfile(bundled) else "ffmpeg"

FFMPEG = ffmpeg_executable()


# ─── CUDA DETECTION ──────────────────────────────────────────────────────────
def check_nvenc_available():
    """Cek apakah FFmpeg build ini punya NVENC support."""
    try:
        result = subprocess.run(
            [FFMPEG, "-encoders"],
            capture_output=True, text=True
        )
        return "h264_nvenc" in result.stdout
    except FileNotFoundError:
        return False

def check_cuda_hwaccel():
    """Cek apakah CUDA hwaccel tersedia untuk decode."""
    try:
        result = subprocess.run(
            [FFMPEG, "-hwaccels"],
            capture_output=True, text=True
        )
        return "cuda" in result.stdout
    except FileNotFoundError:
        return False


class BlackVueMerger:
    def __init__(self, root):
        self.root = root
        self.root.title("BlackVue PiP Merger  //  CUDA Edition")
        self.root.geometry("760x820")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.folder_var    = tk.StringVar()
        self.output_var    = tk.StringVar()
        self.pip_size_var  = tk.StringVar(value="320x180")
        self.pip_pos_var   = tk.StringVar(value="Kiri Atas")
        self.encoder_var   = tk.StringVar(value="auto")   # auto / nvenc / cpu
        self.hwdec_var     = tk.BooleanVar(value=True)    # hardware decode
        self.preset_var    = tk.StringVar(value="p4")     # NVENC preset
        self.cq_var        = tk.StringVar(value="23")     # quality
        self.running       = False

        # Deteksi kapabilitas GPU saat startup
        self.nvenc_ok  = check_nvenc_available()
        self.hwdec_ok  = check_cuda_hwaccel()

        self._build_ui()
        self._show_gpu_status()

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=ACCENT2, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="◈  BLACKVUE PiP MERGER  //  CUDA",
                 font=("Courier New", 15, "bold"),
                 bg=ACCENT2, fg="white").pack(side="left", padx=18, pady=14)
        self.gpu_badge = tk.Label(hdr, text="⬛ GPU: Checking...",
                 font=FONT_LOG, bg=ACCENT2, fg="#cce8f0")
        self.gpu_badge.pack(side="right", padx=18)

        # Body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # ── 01 Folder ──
        self._section(body, "01  FOLDER VIDEO")
        row1 = tk.Frame(body, bg=BG)
        row1.pack(fill="x", pady=(0, 10))
        self._entry(row1, self.folder_var).pack(side="left", fill="x", expand=True)
        self._btn(row1, "PILIH", self._pick_folder, ACCENT).pack(side="left", padx=(8,0))

        # ── 02 Output ──
        self._section(body, "02  FILE OUTPUT")
        row2 = tk.Frame(body, bg=BG)
        row2.pack(fill="x", pady=(0, 10))
        self._entry(row2, self.output_var).pack(side="left", fill="x", expand=True)
        self._btn(row2, "PILIH", self._pick_output, ACCENT).pack(side="left", padx=(8,0))

        # ── 03 PiP Options ──
        self._section(body, "03  OPSI PiP")
        opt = tk.Frame(body, bg=BG)
        opt.pack(fill="x", pady=(0, 6))

        tk.Label(opt, text="Ukuran PiP :", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(side="left")
        ttk.Combobox(opt, textvariable=self.pip_size_var,
                     values=["320x180","426x240","480x270","560x315","640x360"],
                     width=12, state="readonly", font=FONT_BODY
                     ).pack(side="left", padx=(6, 20))

        tk.Label(opt, text="Posisi :", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(side="left")
        ttk.Combobox(opt, textvariable=self.pip_pos_var,
                     values=["Kiri Atas","Kanan Atas","Kiri Bawah","Kanan Bawah"],
                     width=14, state="readonly", font=FONT_BODY
                     ).pack(side="left", padx=(6, 0))

        # ── 04 GPU / Encoder Options ──
        self._section(body, "04  ENCODER  //  GPU SETTINGS")
        enc_frame = tk.Frame(body, bg=PANEL, bd=0, relief="flat")
        enc_frame.pack(fill="x", pady=(0, 10), ipady=8, ipadx=10)

        # Row A: Encoder selector
        rowA = tk.Frame(enc_frame, bg=PANEL)
        rowA.pack(fill="x", padx=10, pady=(6, 4))

        tk.Label(rowA, text="Encoder :", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        for val, lbl in [("auto","AUTO DETECT"), ("nvenc","NVENC  (GPU)"), ("cpu","libx264  (CPU)")]:
            tk.Radiobutton(rowA, text=lbl, variable=self.encoder_var, value=val,
                           font=FONT_LOG, bg=PANEL, fg=TEXT,
                           selectcolor=PANEL, activebackground=PANEL,
                           activeforeground=GPU_COLOR).pack(side="left", padx=(12,0))

        # Row B: HW Decode toggle
        rowB = tk.Frame(enc_frame, bg=PANEL)
        rowB.pack(fill="x", padx=10, pady=(0, 4))
        tk.Checkbutton(rowB, text="Hardware Decode  (CUDA)  — kurangi beban CPU saat baca video",
                       variable=self.hwdec_var,
                       font=FONT_LOG, bg=PANEL, fg=TEXT,
                       selectcolor=PANEL, activebackground=PANEL).pack(side="left")

        # Row C: NVENC preset & quality
        rowC = tk.Frame(enc_frame, bg=PANEL)
        rowC.pack(fill="x", padx=10, pady=(0, 6))

        tk.Label(rowC, text="NVENC Preset :", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        ttk.Combobox(rowC, textvariable=self.preset_var,
                     values=["p1 (Fastest)","p2","p3","p4 (Balanced)","p5","p6","p7 (Best Quality)"],
                     width=18, state="readonly", font=FONT_LOG
                     ).pack(side="left", padx=(6, 20))

        tk.Label(rowC, text="CQ / CRF :", font=FONT_BODY, bg=PANEL, fg=SUBTEXT).pack(side="left")
        ttk.Combobox(rowC, textvariable=self.cq_var,
                     values=["18","20","23","26","28"],
                     width=6, state="readonly", font=FONT_LOG
                     ).pack(side="left", padx=(6, 0))
        tk.Label(rowC, text="(18=best quality, 28=smaller file)",
                 font=FONT_LOG, bg=PANEL, fg=SUBTEXT).pack(side="left", padx=(8,0))

        # ── 05 Log ──
        self._section(body, "05  LOG PROSES")
        log_frame = tk.Frame(body, bg=PANEL, bd=1, relief="flat")
        log_frame.pack(fill="both", expand=True, pady=(0, 12))
        self.log = tk.Text(log_frame, bg=PANEL, fg=TEXT, font=FONT_LOG,
                           height=9, wrap="word", bd=0, padx=8, pady=6,
                           state="disabled", insertbackground=ACCENT)
        sb = tk.Scrollbar(log_frame, command=self.log.yview, bg=PANEL)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        # ── Progress + Button ──
        self.progress = ttk.Progressbar(body, mode="indeterminate", length=720)
        self.progress.pack(fill="x", pady=(0, 10))
        self.run_btn = self._btn(body, "▶  MULAI PROSES", self._start, SUCCESS, full=True)
        self.run_btn.pack(fill="x")

        # ttk style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL,
                        foreground=TEXT, selectbackground=ACCENT2)
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL,
                        background=ACCENT, thickness=6)

    def _section(self, parent, title):
        tk.Label(parent, text=title, font=("Courier New", 9, "bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w", pady=(6,3))

    def _entry(self, parent, var):
        return tk.Entry(parent, textvariable=var, font=FONT_BODY,
                        bg=PANEL, fg=TEXT, insertbackground=ACCENT,
                        relief="flat", bd=6)

    def _btn(self, parent, text, cmd, color=ACCENT, full=False):
        return tk.Button(parent, text=text, command=cmd,
                         font=("Courier New", 10, "bold"),
                         bg=color, fg="white", activebackground=ACCENT2,
                         activeforeground="white", relief="flat",
                         bd=0, padx=14, pady=8, cursor="hand2")

    # ── GPU STATUS ────────────────────────────────────────────────────────────
    def _show_gpu_status(self):
        if self.nvenc_ok:
            self.gpu_badge.configure(
                text="🟢 RTX 4060  NVENC READY",
                fg="#00c896"
            )
            self._log("🟢 NVENC tersedia — encoding akan pakai GPU RTX 4060", SUCCESS)
        else:
            self.gpu_badge.configure(
                text="🔴 NVENC tidak tersedia",
                fg=DANGER
            )
            self._log("🔴 NVENC tidak ditemukan — fallback ke CPU (libx264)", WARNING)
            self._log("   Pastikan FFmpeg versi full/shared build dari https://ffmpeg.org", SUBTEXT)

        if self.hwdec_ok:
            self._log("✅ CUDA hwaccel tersedia — hardware decode aktif", SUCCESS)
        else:
            self._log("⚠️  CUDA hwaccel tidak tersedia — decode pakai CPU", WARNING)

    # ── ACTIONS ───────────────────────────────────────────────────────────────
    def _pick_folder(self):
        d = filedialog.askdirectory(title="Pilih folder video BlackVue")
        if d:
            self.folder_var.set(d)
            self.output_var.set(os.path.join(d, "OUTPUT_GABUNG.mp4"))
            self._scan_folder(d)

    def _pick_output(self):
        f = filedialog.asksaveasfilename(
            title="Simpan output sebagai",
            defaultextension=".mp4",
            filetypes=[("MP4 Video", "*.mp4")])
        if f:
            self.output_var.set(f)

    def _scan_folder(self, folder):
        ef = sorted(glob.glob(os.path.join(folder, "*_EF.mp4")))
        er = sorted(glob.glob(os.path.join(folder, "*_ER.mp4")))
        self._log(f"\n📁 Folder  : {folder}", ACCENT)
        self._log(f"🎥 Front (EF) : {len(ef)} file")
        self._log(f"🎥 Rear  (ER) : {len(er)} file")
        pairs = self._get_pairs(folder)
        self._log(f"✅ Pasangan valid : {len(pairs)} pasang", SUCCESS)
        if len(pairs) == 0:
            self._log("⚠️  Tidak ada pasangan EF+ER ditemukan!", WARNING)

    def _get_pairs(self, folder):
        pairs = []
        for ef in sorted(glob.glob(os.path.join(folder, "*_EF.mp4"))):
            base = os.path.basename(ef).replace("_EF.mp4", "")
            er   = os.path.join(folder, base + "_ER.mp4")
            if os.path.exists(er):
                pairs.append((ef, er, base))
        return pairs

    def _get_pip_offset(self, pos):
        return {
            "Kiri Atas"   : "10:10",
            "Kanan Atas"  : "main_w-overlay_w-10:10",
            "Kiri Bawah"  : "10:main_h-overlay_h-10",
            "Kanan Bawah" : "main_w-overlay_w-10:main_h-overlay_h-10",
        }.get(pos, "10:10")

    # ── ENCODER LOGIC ─────────────────────────────────────────────────────────
    def _resolve_encoder(self):
        """Tentukan encoder yang akan dipakai berdasarkan setting & ketersediaan."""
        sel = self.encoder_var.get()
        if sel == "nvenc":
            if self.nvenc_ok:
                return "nvenc"
            else:
                self._log("⚠️  NVENC dipilih tapi tidak tersedia, fallback ke CPU", WARNING)
                return "cpu"
        elif sel == "cpu":
            return "cpu"
        else:  # auto
            return "nvenc" if self.nvenc_ok else "cpu"

    def _build_ffmpeg_cmd(self, ef, er, pip_w, pip_h, pip_pos, temp_out, encoder):
        """Buat command FFmpeg dengan atau tanpa CUDA."""
        use_hwdec = self.hwdec_var.get() and self.hwdec_ok

        # Preset parsing (ambil hanya "p4" dari "p4 (Balanced)")
        preset_raw = self.preset_var.get().split(" ")[0]
        cq         = self.cq_var.get()

        if encoder == "nvenc":
            # ── FULL GPU PATH ──────────────────────────────────────────────
            # Decode: CUDA hwaccel (opsional)
            # Scale PiP: scale_cuda (tetap di VRAM)
            # Overlay: download ke RAM (overlay filter belum full CUDA)
            # Encode: h264_nvenc

            hwdec_flags = []
            if use_hwdec:
                hwdec_flags = [
                    "-hwaccel", "cuda",
                    "-hwaccel_output_format", "cuda",
                ]

            if use_hwdec:
                # Frame EF ada di VRAM (format cuda), perlu download dulu untuk overlay
                # ER juga di-hwdec, lalu scale_cuda, lalu download
                filter_complex = (
                    f"[0:v]hwdownload,format=nv12,format=yuv420p[front];"
                    f"[1:v]hwdownload,format=nv12,format=yuv420p,"
                    f"scale={pip_w}:{pip_h}[pip];"
                    f"[front][pip]overlay={pip_pos}[v]"
                )
            else:
                filter_complex = (
                    f"[1:v]scale={pip_w}:{pip_h}[pip];"
                    f"[0:v][pip]overlay={pip_pos}[v]"
                )

            cmd = (
                hwdec_flags +
                ["-i", ef] +
                hwdec_flags +
                ["-i", er,
                 "-filter_complex", filter_complex,
                 "-map", "[v]",
                 "-map", "0:a",
                 "-c:v", "h264_nvenc",
                 "-preset", preset_raw,
                 "-cq", cq,
                 "-b:v", "0",          # VBR mode dengan CQ
                 "-rc", "vbr",
                 "-c:a", "aac",
                 "-y", temp_out]
            )
            return [FFMPEG] + cmd

        else:
            # ── CPU PATH (libx264) ─────────────────────────────────────────
            filter_complex = (
                f"[1:v]scale={pip_w}:{pip_h}[pip];"
                f"[0:v][pip]overlay={pip_pos}[v]"
            )
            return [
                FFMPEG, "-y",
                "-i", ef,
                "-i", er,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "0:a",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", cq,
                "-c:a", "aac",
                temp_out
            ]

    # ── MAIN PROCESS ──────────────────────────────────────────────────────────
    def _start(self):
        if self.running:
            return
        folder = self.folder_var.get().strip()
        output = self.output_var.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Pilih folder video terlebih dahulu!")
            return
        if not output:
            messagebox.showerror("Error", "Tentukan file output terlebih dahulu!")
            return
        try:
            subprocess.run([FFMPEG, "-version"], capture_output=True, check=True)
        except FileNotFoundError:
            messagebox.showerror("FFmpeg tidak ditemukan",
                "FFmpeg belum terinstall atau tidak ada di PATH.\n\n"
                "Download di: https://ffmpeg.org/download.html\n"
                "Gunakan versi 'full' build agar NVENC tersedia.\n"
                "Lalu tambahkan ke PATH Windows.")
            return

        self.running = True
        self.run_btn.configure(state="disabled", text="⏳  MEMPROSES...")
        self.progress.start(12)
        threading.Thread(target=self._process,
                         args=(folder, output), daemon=True).start()

    def _process(self, folder, output):
        pairs    = self._get_pairs(folder)
        pip_w, pip_h = self.pip_size_var.get().split("x")
        pip_pos  = self._get_pip_offset(self.pip_pos_var.get())
        encoder  = self._resolve_encoder()
        temp_files = []
        temp_list  = os.path.join(folder, "_temp_list.txt")

        enc_label = f"h264_nvenc (RTX 4060)" if encoder == "nvenc" else "libx264 (CPU)"
        self._log(f"\n🚀 Memulai proses {len(pairs)} pasang video", ACCENT)
        self._log(f"🔧 Encoder  : {enc_label}", GPU_COLOR if encoder == "nvenc" else WARNING)
        self._log(f"🔧 HW Decode: {'CUDA' if (self.hwdec_var.get() and self.hwdec_ok) else 'CPU'}\n",
                  GPU_COLOR if (self.hwdec_var.get() and self.hwdec_ok) else SUBTEXT)

        for i, (ef, er, base) in enumerate(pairs, 1):
            temp_out = os.path.join(folder, f"_temp_pip_{base}.mp4")
            self._log(f"[{i}/{len(pairs)}] {base}")

            cmd = self._build_ffmpeg_cmd(ef, er, pip_w, pip_h, pip_pos, temp_out, encoder)
            self._log(f"   CMD: {' '.join(cmd[:8])} ...", SUBTEXT)

            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    temp_files.append(temp_out)
                    self._log(f"   ✅ OK", SUCCESS)
                else:
                    # Jika NVENC gagal, coba fallback CPU otomatis
                    if encoder == "nvenc":
                        self._log(f"   ⚠️  NVENC gagal, retry dengan CPU...", WARNING)
                        cmd_cpu = self._build_ffmpeg_cmd(
                            ef, er, pip_w, pip_h, pip_pos, temp_out, "cpu")
                        result2 = subprocess.run(cmd_cpu, capture_output=True, text=True)
                        if result2.returncode == 0:
                            temp_files.append(temp_out)
                            self._log(f"   ✅ OK (CPU fallback)", WARNING)
                        else:
                            self._log(f"   ❌ Gagal: {result2.stderr[-300:]}", DANGER)
                    else:
                        self._log(f"   ❌ Gagal: {result.stderr[-300:]}", DANGER)
            except Exception as e:
                self._log(f"   ❌ Error: {e}", DANGER)

        if not temp_files:
            self._log("\n❌ Tidak ada video berhasil diproses.", DANGER)
            self._done()
            return

        # Concat
        self._log(f"\n📎 Menggabungkan {len(temp_files)} video menjadi 1 file...")
        with open(temp_list, "w") as f:
            for t in temp_files:
                f.write(f"file '{t}'\n")

        concat_cmd = [
            FFMPEG, "-y", "-f", "concat", "-safe", "0",
            "-i", temp_list, "-c", "copy", output
        ]
        result = subprocess.run(concat_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            size_mb = os.path.getsize(output) / (1024 * 1024)
            self._log(f"\n✅ SELESAI!", SUCCESS)
            self._log(f"📄 Output : {output}", ACCENT)
            self._log(f"💾 Ukuran : {size_mb:.1f} MB", ACCENT)
        else:
            self._log(f"\n❌ Gagal concat: {result.stderr[-300:]}", DANGER)

        # Cleanup
        for t in temp_files:
            try: os.remove(t)
            except: pass
        try: os.remove(temp_list)
        except: pass

        self._done()

    def _done(self):
        self.running = False
        self.root.after(0, lambda: [
            self.progress.stop(),
            self.run_btn.configure(state="normal", text="▶  MULAI PROSES")
        ])

    def _log(self, msg, color=TEXT):
        def _write():
            self.log.configure(state="normal")
            tag = f"color_{color.replace('#','')}"
            self.log.insert("end", msg + "\n", tag)
            self.log.tag_configure(tag, foreground=color)
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(0, _write)


if __name__ == "__main__":
    root = tk.Tk()
    app  = BlackVueMerger(root)
    root.mainloop()
