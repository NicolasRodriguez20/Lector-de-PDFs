from tkinter import messagebox,filedialog
import tkinter as tk
import threading
import os
_BG        = "#12121f"
_BG_WIN    = "#1a1a2e"
_BG_DROP   = "#16162a"
_BG_LIST   = "#1e1e30"
_BORDER    = "#2e2e50"
_FG        = "#e8e8f0"
_FG_DIM    = "#7a7a9a"
_TEAL      = "#00c2a0"
_TEAL_H    = "#00d9b3"
_RED       = "#e53935"
_RED_H     = "#ef5350"
_BTN_BG    = "#252540"
_BTN_H     = "#2e2e50"
class imagenes:
    def __init__(self,ui):
        self.ui = ui
    def abrir_cargar_ventana(self):
        if (hasattr(self.ui, "cargar_ventana")
                and self.ui.cargar_ventana is not None
                and tk.Toplevel.winfo_exists(self.ui.cargar_ventana)):
            messagebox.showinfo("Atención", "La ventana de carga ya está abierta.")
            return

        self.ui.btn_select.config(state=tk.DISABLED)
        self.ui.btn_cargar.config(state=tk.DISABLED)

        win = tk.Toplevel(self.ui.root)
        self.ui.cargar_ventana = win
        win.title("Pega imágenes (Ctrl+V)")
        win.configure(bg=_BG_WIN)
        win.resizable(False, False)

        w, h = 600, 440
        win.update_idletasks()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        win.protocol("WM_DELETE_WINDOW", self.cerrar_cargar_ventana)

        info_frame = tk.Frame(win, bg=_BG_WIN)
        info_frame.pack(fill=tk.X, padx=24, pady=(18, 10))
        tk.Label(info_frame, text="ⓘ", bg=_BG_WIN, fg=_FG_DIM,
                font=("Segoe UI", 12)).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(info_frame,
                text="Pega imágenes con Ctrl+V o selecciona archivos.",
                bg=_BG_WIN, fg=_FG_DIM,
                font=("Segoe UI", 11)).pack(side=tk.LEFT)

        drop_frame = tk.Frame(win, bg=_BG_DROP,
                            highlightthickness=2,
                            highlightbackground=_BORDER,
                            highlightcolor=_BORDER)
        drop_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 16))

        self._icon_canvas = tk.Canvas(drop_frame, bg=_BG_DROP,
                                    highlightthickness=0, width=120, height=120)
        self._icon_canvas.pack(expand=True, pady=20)
        self._draw_clipboard_icon(self._icon_canvas)

        self._list_frame = tk.Frame(drop_frame, bg=_BG_DROP)
        self.ui.listbox = tk.Listbox(
            self._list_frame,
            bg=_BG_LIST, fg=_FG,
            selectbackground="#3a3a5c", selectforeground=_FG,
            relief=tk.FLAT, bd=0,
            font=("Segoe UI", 10),
            highlightthickness=0,
            activestyle="none",
        )
        self.ui.listbox.pack(fill=tk.BOTH, expand=True)

        btn_bar = tk.Frame(win, bg=_BG_WIN)
        btn_bar.pack(fill=tk.X, padx=24, pady=(0, 20))

        self._make_btn(btn_bar, "📋  Pegar (Ctrl+V)",
                    self.paste_from_clipboard,
                    _TEAL, _TEAL_H).pack(side=tk.LEFT, padx=(0, 8))

        self._make_btn(btn_bar, "📁  Seleccionar archivo(s)...",
                    self.seleccionar_archivos,
                    _BTN_BG, _BTN_H,
                    border=True).pack(side=tk.LEFT, padx=(0, 8))

        self._make_btn(btn_bar, "✕  Cerrar",
                    self.cerrar_cargar_ventana,
                    _RED, _RED_H).pack(side=tk.RIGHT)

        for seq in ("<Control-v>", "<Control-V>", "<Command-v>", "<Command-V>"):
            win.bind(seq, self._on_ctrl_v)

    def _make_btn(self, parent, text, command, bg, hover, border=False):
        kw = dict(
            text=text, command=command,
            bg=bg, fg=_FG,
            activebackground=hover, activeforeground=_FG,
            relief=tk.FLAT, bd=0, cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=16, pady=10,
            highlightthickness=1 if border else 0,
            highlightbackground=_BORDER if border else bg,
        )
        btn = tk.Button(parent, **kw)
        btn.bind("<Enter>", lambda _e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
        return btn

    def _draw_clipboard_icon(self, canvas):
        """Dibuja un ícono de portapapeles + lupa en tonos grises."""
        c = canvas
        c.delete("all")
        c.create_rectangle(25, 30, 85, 100, fill="#3a3a5c", outline="#5a5a7a", width=2)
        c.create_rectangle(42, 22, 68, 36, fill="#4a4a6a", outline="#5a5a7a", width=1)
        for y in [50, 62, 74]:
            c.create_line(34, y, 76, y, fill="#6a6a8a", width=2)
        c.create_oval(62, 60, 92, 90, outline="#8888aa", width=3, fill="#2a2a44")
        c.create_line(88, 86, 102, 100, fill="#8888aa", width=4, capstyle="round")
        c.create_rectangle(34, 48, 60, 78, fill="#2a2a44", outline="#5a5a7a")
        c.create_polygon(34, 78, 46, 62, 54, 70, 60, 62, 60, 78, fill="#3a4a6a")

    def _show_list(self):
        """Cambia del ícono a la lista cuando hay items."""
        self._icon_canvas.pack_forget()
        self._list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _on_ctrl_v(self, event=None):
        self.ui.imagen.paste_from_clipboard()
        return "break"

    def seleccionar_archivos(self):
        rutas = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp")]
        )
        for ruta in rutas:
            try:
                from PIL import Image
                img = Image.open(ruta)
                self.ui.listbox.insert(tk.END, f"Archivo: {os.path.basename(ruta)}")
                threading.Thread(target=self.ui.imagen._ocr_and_insert, args=(img,)).start()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir {ruta}.\n{e}")

    def paste_from_clipboard(self):
        from PIL import ImageGrab, Image, ImageTk
        import io, os
        try:
            clip = ImageGrab.grabclipboard()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo acceder al portapapeles: {e}")
            return

        if isinstance(clip, Image.Image):
            self.ui.paste_count += 1
            self.ui.listbox.insert(tk.END, f"Imagen pegada (#{self.ui.paste_count})")
            threading.Thread(target=self.ui.imagen._ocr_and_insert, args=(clip,)).start()
            return

        if isinstance(clip, list):
            for path in clip:
                if os.path.isfile(path):
                    try:
                        img = Image.open(path)
                        self.ui.listbox.insert(tk.END, f"Archivo pegado: {os.path.basename(path)}")
                        threading.Thread(target=self.ui.imagen._ocr_and_insert, args=(img,)).start()
                    except Exception as e:
                        self.ui.listbox.insert(tk.END, f"Error abriendo {path}: {e}")

    def _ocr_and_insert(self, pil_image):
        import pytesseract        

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        try:
            texto = pytesseract.image_to_string(pil_image, lang="spa").strip()
            if not texto:
                texto = "[No se detectó texto en la imagen]"
        except Exception as e:
            texto = f"[Error en OCR: {e}]"

        def insertar():
            self.ui.text_display.insert(tk.END, texto + "\n\n")
            self.ui.text_display.see(tk.END)
            self.ui.lector.on_text_modified()
            if self.ui.engine and self.ui.text_blocks:
                self.ui.btn_read.config(state=tk.NORMAL)
        self.ui.root.after(0, insertar)

    def cerrar_cargar_ventana(self):
        if hasattr(self.ui, "cargar_ventana") and self.ui.cargar_ventana:
            self.ui.cargar_ventana.destroy()
        self.ui.cargar_ventana = None

        self.ui.btn_read.config(state=tk.NORMAL)
        self.ui.btn_cargar.config(state=tk.NORMAL)
        self.ui.btn_select.config(state=tk.NORMAL)
