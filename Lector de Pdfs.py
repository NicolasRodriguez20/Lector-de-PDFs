import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\casatres\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
from lectura import Lectura
from pdfs import Pdfs
from historial import historial
from imagenes import imagenes
# ── Paleta de colores (tema oscuro) ──────────────────────────────────────────
BG_DARK      = "#12121f"   # fondo principal
BG_TOOLBAR   = "#1a1a2e"   # barra superior
BG_MID       = "#1e1e30"   # fondo área texto
FG_WHITE     = "#e8e8f0"   # texto general
FG_DIM       = "#7a7a9a"   # texto secundario
ACCENT_TEAL  = "#00c2a0"   # verde-azulado (progreso, botón cargar)
ACCENT_BLUE  = "#2979ff"   # azul (leer/continuar)
ACCENT_RED   = "#e53935"   # rojo (terminar)
ACCENT_GOLD  = "#ffd740"   # ámbar (velocidad activa)
ACCENT_PURP  = "#7c4dff"   # violeta (voz)
ACCENT_GREY  = "#455a64"   # gris (historial borrar)
ACCENT_NAVY  = "#3d5afe"   # azul oscuro (ver historial)
BTN_BG       = "#252540"   # fondo botones normales
BTN_HOVER    = "#2e2e50"   # hover botones
def apply_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Dark.Horizontal.TProgressbar",
        troughcolor=BG_MID,
        background=ACCENT_TEAL,
        bordercolor=BG_DARK,
        lightcolor=ACCENT_TEAL,
        darkcolor=ACCENT_TEAL,
        thickness=8,
    )
class PDFReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lector de PDF con Marcador Inteligente")
        self.root.geometry("1050x720")
        self.root.configure(bg=BG_DARK)
        self.root.minsize(800, 550)
        apply_styles()
        self.HISTORY_FILE = os.path.join(
            os.path.expanduser("~"), "Documents", "pdf_reader_history.json"
        )
        self.pdf_path        = ""
        self.is_reading      = False
        self.text_blocks     = []
        self.current_block_index   = 0
        self.original_text_blocks  = []
        self.engine          = None
        self.normal_speed    = 150
        self.fast_speed      = 300
        self.current_speed   = self.normal_speed
        self.history_window  = None
        self.historial = historial(self)
        self.lector    = Lectura(self)
        self.pdf       = Pdfs(self)
        self.imagen    = imagenes(self)
        self.create_widgets()
        self.setup_voice_engine()
        self.paste_count = 0
        self.history = self.pdf.load_history()
        self.root.protocol("WM_DELETE_WINDOW", self.lector.on_closing)
    def setup_voice_engine(self):
        try:
            from tts import EdgeTTSVoice
            self.engine = EdgeTTSVoice()
            self.audio_status.config(text="edge-tts activo (voz natural)", fg=ACCENT_TEAL)
        except Exception as e:
            print("Fallo edge-tts, usando pyttsx3:", e)
            try:
                from tts import Pyttsx3Voice
                self.engine = Pyttsx3Voice()
                self.audio_status.config(text="pyttsx3 activo (voz robótica offline)", fg=ACCENT_GOLD)
            except Exception as e2:
                messagebox.showerror("Error", f"No se pudo iniciar ningún motor:\n{e2}")
                self.engine = None
    def _make_btn(self, parent, text, command, bg, fg=FG_WHITE,
                  state=tk.NORMAL, width=None, padx=10, pady=5, font=("Segoe UI", 9, "bold")):
        kw = dict(
            text=text, command=command, bg=bg, fg=fg,
            activebackground=bg, activeforeground=fg,
            relief=tk.FLAT, cursor="hand2",
            state=state, font=font,
            padx=padx, pady=pady,
            bd=0, highlightthickness=0,
        )
        if width:
            kw["width"] = width
        btn = tk.Button(parent, **kw)
        def on_enter(e, b=btn, orig=bg):
            if b["state"] != tk.DISABLED:
                b.config(bg=self._lighten(orig))
        def on_leave(e, b=btn, orig=bg):
            if b["state"] != tk.DISABLED:
                b.config(bg=orig)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn
    @staticmethod
    def _lighten(hex_color, amount=20):
        """Aclara un color hex en `amount` unidades RGB."""
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, r + amount)
            g = min(255, g + amount)
            b = min(255, b + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color
    def create_widgets(self):
        toolbar = tk.Frame(self.root, bg=BG_TOOLBAR, pady=6)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        sep = tk.Frame(self.root, bg="#0a0a18", height=2)
        sep.pack(fill=tk.X, side=tk.TOP)
        left_group = tk.Frame(toolbar, bg=BG_TOOLBAR)
        left_group.pack(side=tk.LEFT, padx=(8, 0))
        self.btn_select = self._make_btn(
            left_group, "📂  Archivo", self.pdf.select_file, BTN_BG
        )
        self.btn_select.pack(side=tk.LEFT, padx=3)
        self.btn_read = self._make_btn(
            left_group, "▶  Leer", self.lector.toggle_reading,
            ACCENT_BLUE, state=tk.DISABLED
        )
        self.btn_read.pack(side=tk.LEFT, padx=3)
        self.btn_terminar = self._make_btn(
            left_group, "⏹  Terminar", self.lector.terminar_lectura, ACCENT_RED
        )
        self.btn_terminar.pack(side=tk.LEFT, padx=3)
        self.btn_speed = self._make_btn(
            left_group, "⏩  Velocidad: 1x", self.lector.toggle_speed, BTN_BG
        )
        self.btn_speed.pack(side=tk.LEFT, padx=3)
        self.btn_clear_history = self._make_btn(
            left_group, "🗑  Historial", self.historial.clear_history, ACCENT_GREY
        )
        self.btn_clear_history.pack(side=tk.LEFT, padx=3)
        self.btn_view_history = self._make_btn(
            left_group, "👁  Ver Historial", self.historial.show_history_window, ACCENT_NAVY
        )
        self.btn_view_history.pack(side=tk.LEFT, padx=3)
        self.btn_voice = self._make_btn(
            left_group, "🔵  Voz", self.toggle_voice, ACCENT_PURP
        )
        self.btn_voice.pack(side=tk.LEFT, padx=3)
        right_group = tk.Frame(toolbar, bg=BG_TOOLBAR)
        right_group.pack(side=tk.RIGHT, padx=(0, 10))
        self.btn_prev = self._make_btn(
            right_group, "❮", self.lector.previous_block,
            BTN_BG, padx=8, pady=4
        )
        self.btn_prev.pack(side=tk.LEFT, padx=2)
        self.btn_next = self._make_btn(
            right_group, "❯", self.lector.next_block,
            BTN_BG, padx=8, pady=4
        )
        self.btn_next.pack(side=tk.LEFT, padx=2)
        counter_frame = tk.Frame(right_group, bg=BG_TOOLBAR)
        counter_frame.pack(side=tk.LEFT, padx=(8, 4))
        self.block_counter = tk.Label(
            counter_frame,
            text="Pág 0 / 0",
            font=("Segoe UI", 10, "bold"),
            bg=BG_TOOLBAR, fg=FG_WHITE
        )
        self.block_counter.pack(anchor="e")
        self.saved_position_marker = tk.Label(
            counter_frame,
            text="",
            font=("Segoe UI", 8),
            bg=BG_TOOLBAR, fg=ACCENT_TEAL
        )
        self.saved_position_marker.pack(anchor="e")
        status_bar = tk.Frame(self.root, bg=BG_DARK, pady=3)
        status_bar.pack(fill=tk.X)
        self.audio_status = tk.Label(
            status_bar,
            text="Estado del audio: inicializando...",
            font=("Segoe UI", 9),
            bg=BG_DARK, fg=FG_DIM
        )
        self.audio_status.pack()
        mid_row = tk.Frame(self.root, bg=BG_DARK, pady=4)
        mid_row.pack(fill=tk.X, padx=10)
        self.progress = ttk.Progressbar(
            mid_row,
            orient=tk.HORIZONTAL,
            mode="determinate",
            style="Dark.Horizontal.TProgressbar",
        )
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.btn_cargar = self._make_btn(
            mid_row,
            "📋  Cargar / Pegar Imágenes (Ctrl+V)",
            self.imagen.abrir_cargar_ventana,
            ACCENT_TEAL, fg="#000000",
            padx=12, pady=6,
        )
        self.btn_cargar.pack(side=tk.RIGHT)
        # ── ÁREA DE TEXTO ─────────────────────────────────────────────────
        text_frame = tk.Frame(self.root, bg=BG_DARK)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))
        self.text_display = ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 12),
            bg=BG_MID,
            fg=FG_WHITE,
            insertbackground=FG_WHITE,
            selectbackground="#3a3a5c",
            selectforeground=FG_WHITE,
            padx=14,
            pady=10,
            relief=tk.FLAT,
            bd=0,
            spacing1=4,  
            spacing3=4,  
        )
        self.text_display.pack(fill=tk.BOTH, expand=True)
        self.text_display.vbar.config(
            bg=BG_MID,
            troughcolor=BG_DARK,
            activebackground=ACCENT_TEAL,
            width=10,
            relief=tk.FLAT,
            bd=0,
        )
        self.text_display.tag_config(
            "highlight",
            background="#c8a800",   
            foreground="#000000",
        )
        self.text_display.tag_config(
            "saved",
            background="#00695c",  
            foreground="#ffffff",
        )
        # Eventos
        self.text_display.bind("<KeyRelease>", self.lector.on_text_modified)
    def toggle_voice(self):
        try:
            from tts import EdgeTTSVoice, Pyttsx3Voice
            if isinstance(self.engine, EdgeTTSVoice):
                self.engine.stop()
                self.engine = Pyttsx3Voice()
                self.audio_status.config(text="pyttsx3 activo (robot)", fg=ACCENT_GOLD)
            else:
                self.engine.stop()
                self.engine = EdgeTTSVoice()
                self.audio_status.config(text="edge-tts activo (natural)", fg=ACCENT_TEAL)
        except Exception as e:
            messagebox.showerror("Error", str(e))
def _patched_update_ui(self_lector):
    total   = len(self_lector.ui.text_blocks)
    current = self_lector.ui.current_block_index + 1 if total > 0 else 0
    self_lector.ui.block_counter.config(text=f"Pág {current} / {total}")
    if self_lector.ui.pdf_path in self_lector.ui.history:
        saved_pos = self_lector.ui.history[self_lector.ui.pdf_path]["position"]
        self_lector.ui.saved_position_marker.config(
            text=f"Guardado: {saved_pos + 1}/{total}",
            fg=ACCENT_TEAL,
        )
        self_lector.ui.historial.highlight_saved_position(saved_pos)
    else:
        self_lector.ui.saved_position_marker.config(text="")
from lectura import Lectura as _Lectura
_Lectura.update_ui = _patched_update_ui
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReaderApp(root)
    if not app.engine:
        messagebox.showwarning(
            "Advertencia",
            "No se encontró un motor de voz funcional. El programa no podrá leer en voz alta.",
        )
    root.mainloop()