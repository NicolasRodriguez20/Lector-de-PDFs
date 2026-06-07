import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\casatres\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

class historial:
    def __init__(self,ui):
        self.ui = ui
        self.colors = {
            "bg": "#0d1117",
            "top": "#151a24",
            "panel": "#111821",
            "row": "#171d26",
            "row_alt": "#1b222c",
            "row_selected": "#5b646f",
            "border": "#3b4654",
            "text": "#f2f5f8",
            "muted": "#aeb7c2",
            "search": "#242b35",
            "green": "#16a979",
            "green_hover": "#1dc48d",
            "red": "#b64e52",
            "red_hover": "#cc5b60",
            "blue": "#1e9fbd",
            "blue_hover": "#25b6d8",
            "button": "#121822",
            "button_hover": "#1c2430",
        }
    def _center_window(self, win, width, height):
        win.update_idletasks()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def _make_button(self, parent, text, command, bg, hover_bg, width=None):
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            activebackground=hover_bg,
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            width=width,
            cursor="hand2",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#5b6674",
            highlightcolor="#5b6674",
        )
        btn.bind("<Enter>", lambda _e: btn.config(bg=hover_bg))
        btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
        return btn

    def _normalize_history_items(self):

        items = list(self.ui.history.items())

        if not hasattr(self, "history_search_var"):
            self.history_filtered_items = items
            return

        query = self.history_search_var.get().strip().lower()

        if query == "buscar en el historial...":
            query = ""

        if query:
            items = [
                (path, data)
                for path, data in items
                if query in os.path.basename(path).lower()
            ]

        items.sort(
            key=lambda item: item[1].get("timestamp", ""),
            reverse=True
        )

        self.history_filtered_items = items

        total_pages = self._total_history_pages()

        if self.history_page > total_pages:
            self.history_page = total_pages

        if self.history_page < 1:
            self.history_page = 1

    def _total_history_pages(self):
        total = len(self.history_filtered_items)
        return max(1, (total + self.history_page_size - 1) // self.history_page_size)

    def _on_history_search(self, *_args):
        self.history_page = 1
        self._render_history_entries()
    def _style_history_window(self):
        style = ttk.Style(self.ui.history_window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "History.Vertical.TScrollbar",
            gripcount=0,
            background="#9aa1aa",
            darkcolor="#9aa1aa",
            lightcolor="#9aa1aa",
            troughcolor=self.colors["bg"],
            bordercolor=self.colors["bg"],
            arrowcolor=self.colors["bg"],
            relief="flat",
            width=14,
        )
        style.map(
            "History.Vertical.TScrollbar",
            background=[("active", "#c1c7d0")],
        )    
    def _render_history_entries(self):
        if not self.history_list_frame:
            return
        self._normalize_history_items()
        for child in self.history_list_frame.winfo_children():
            child.destroy()

        total_pages = self._total_history_pages()
        start = (self.history_page - 1) * self.history_page_size
        visible_items = self.history_filtered_items[start:start + self.history_page_size]

        if not visible_items:
            tk.Label(
                self.history_list_frame,
                text="No se encontraron resultados",
                bg=self.colors["bg"], fg=self.colors["muted"],
                font=("Segoe UI", 14),
            ).pack(pady=80)
        else:
            for index, (pdf_path, data) in enumerate(visible_items):
                self._create_history_row(pdf_path, data, index)

        if self.history_page_label:
            self.history_page_label.config(text=f"Pág {self.history_page} / {total_pages}")
        if self.history_prev_btn:
            self.history_prev_btn.config(state=tk.NORMAL if self.history_page > 1 else tk.DISABLED)
        if self.history_next_btn:
            self.history_next_btn.config(state=tk.NORMAL if self.history_page < total_pages else tk.DISABLED)

    def _create_history_row(self, pdf_path, data, index):
        filename = os.path.basename(pdf_path)
        total = data.get("total_blocks", 0)
        pos = data.get("position", 0) + 1
        timestamp = data.get("timestamp", "")
        is_current = self.ui.pdf_path == pdf_path

        row_bg = self.colors["row_selected"] if is_current else (
            self.colors["row"] if index % 2 == 0 else self.colors["row_alt"]
        )
        row = tk.Frame(
            self.history_list_frame, bg=row_bg,
            highlightthickness=1, highlightbackground=self.colors["border"],
        )
        row.pack(fill=tk.X, pady=6)

        text_frame = tk.Frame(row, bg=row_bg)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=9)

        tk.Label(
            text_frame, text=filename, bg=row_bg, fg=self.colors["text"],
            anchor="w", font=("Segoe UI", 15, "bold"),
        ).pack(fill=tk.X)
        tk.Label(
            text_frame, text=f"Pág. {pos}/{total} • {timestamp}",
            bg=row_bg, fg=self.colors["text"],
            anchor="w", font=("Segoe UI", 12),
        ).pack(fill=tk.X, pady=(1, 0))

        actions = tk.Frame(row, bg=row_bg)
        actions.pack(side=tk.RIGHT, padx=12, pady=8)

        self._make_button(
            actions, "☁ Cargar",
            lambda p=pdf_path: self.load_from_history(p),
            self.colors["green"], self.colors["green_hover"],
        ).pack(side=tk.LEFT, padx=4)

        self._make_button(
            actions, "🗑 Eliminar",
            lambda p=pdf_path: self.delete_history_entry(p),
            self.colors["red"], self.colors["red_hover"],
        ).pack(side=tk.LEFT, padx=4)

        self._make_button(
            actions, "✎ Editar",
            lambda p=pdf_path: self.edit_history_entry(p),
            self.colors["blue"], self.colors["blue_hover"],
        ).pack(side=tk.LEFT, padx=4)

    def _prev_history_page(self):
        if self.history_page > 1:
            self.history_page -= 1
            self._render_history_entries()

    def _next_history_page(self):
        if self.history_page < self._total_history_pages():
            self.history_page += 1
            self._render_history_entries()

    def show_history_window(self):
        """Muestra una ventana moderna con historial."""

        if self.ui.history_window and self.ui.history_window.winfo_exists():
            self.ui.history_window.lift()
            self.ui.history_window.focus_force()
            return

        self.ui.btn_view_history.config(state=tk.DISABLED)

        self.ui.history_window = tk.Toplevel(self.ui.root)
        self.ui.history_window.title("Historial de Lectura")

        self._center_window(self.ui.history_window, 1024, 720)

        self.ui.history_window.minsize(860, 560)

        self.ui.history_window.configure(bg=self.colors["bg"])

        self.ui.history_window.protocol(
            "WM_DELETE_WINDOW",
            self.close_history_window,
        )

        self.ui.history_window.bind(
            "<Escape>",
            lambda _e: self.close_history_window()
        )

        self._style_history_window()
        
        if not self.ui.history:
            tk.Label(self.ui.history_window, text="No hay historial guardado").pack(pady=20)
            return

        self.history_search_var = tk.StringVar()

        self.history_page = 1

        self.history_page_size = 7

        self.history_filtered_items = []

        root_frame = tk.Frame(
            self.ui.history_window,
            bg=self.colors["bg"]
        )

        root_frame.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(
            root_frame,
            bg=self.colors["bg"]
        )

        header.pack(
            fill=tk.X,
            padx=36,
            pady=(22, 14)
        )

        self._make_button(
            header,
            "← Volver",
            self.close_history_window,
            self.colors["button"],
            self.colors["button_hover"],
        ).pack(side=tk.LEFT)

        tk.Label(
            header,
            text="Historial de Lectura",
            bg=self.colors["bg"],
            fg=self.colors["text"],
            font=("Segoe UI", 28, "bold"),
        ).pack(side=tk.LEFT, expand=True)

        search_frame = tk.Frame(
            header,
            bg=self.colors["search"],
            highlightthickness=1,
            highlightbackground="#596272",
        )

        search_frame.pack(side=tk.RIGHT)

        tk.Label(
            search_frame,
            text="⌕",
            bg=self.colors["search"],
            fg="#7f8895",
            font=("Segoe UI", 14),
        ).pack(side=tk.LEFT, padx=(10, 0))

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.history_search_var,
            bg=self.colors["search"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            bd=0,
            width=26,
            font=("Segoe UI", 12),
        )

        search_entry.pack(
            side=tk.LEFT,
            ipady=8,
            padx=(6, 12)
        )

        search_entry.insert(0, "Buscar en el historial...")
        search_entry.config(fg="#8b94a0")

        def clear_placeholder(_e):
            if search_entry.get() == "Buscar en el historial...":
                search_entry.delete(0, tk.END)
                search_entry.config(fg=self.colors["text"])

        def restore_placeholder(_e):
            if not search_entry.get():
                search_entry.insert(0, "Buscar en el historial...")
                search_entry.config(fg="#8b94a0")

        def sync_search(*_a):
            if search_entry.get() == "Buscar en el historial...":
                return
            self._on_history_search()

        search_entry.bind("<FocusIn>", clear_placeholder)

        search_entry.bind("<FocusOut>", restore_placeholder)

        if not hasattr(self, "_search_trace_added"):
            self.history_search_var.trace_add("write", sync_search)
            self._search_trace_added = True

        if not self.ui.history:

            tk.Label(
                root_frame,
                text="No hay historial guardado",
                bg=self.colors["bg"],
                fg=self.colors["muted"],
                font=("Segoe UI", 15),
            ).pack(expand=True)

            return

        list_container = tk.Frame(
            root_frame,
            bg=self.colors["bg"]
        )

        list_container.pack(
            fill=tk.BOTH,
            expand=True,
            padx=(36, 18),
            pady=(0, 6),
        )

        canvas = tk.Canvas(
            list_container,
            bg=self.colors["bg"],
            bd=0,
            highlightthickness=0,
        )

        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=canvas.yview,
            style="History.Vertical.TScrollbar",
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
            padx=(10, 0),
        )

        self.history_list_frame = tk.Frame(
            canvas,
            bg=self.colors["bg"]
        )

        canvas_window = canvas.create_window(
            (0, 0),
            window=self.history_list_frame,
            anchor="nw"
        )

        def on_frame_configure(_event):
            canvas.configure(
                scrollregion=canvas.bbox("all")
            )

        self.history_list_frame.bind(
            "<Configure>",
            on_frame_configure
        )

        def on_canvas_configure(event):
            canvas.itemconfig(
                canvas_window,
                width=event.width
            )

        canvas.bind(
            "<Configure>",
            on_canvas_configure
        )

        canvas.bind_all(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(
                int(-1 * (e.delta / 120)),
                "units"
            )
        )

        canvas.bind_all(
            "<Button-4>",
            lambda e: canvas.yview_scroll(-1, "units")
        )

        canvas.bind_all(
            "<Button-5>",
            lambda e: canvas.yview_scroll(1, "units")
        )

        footer = tk.Frame(
            root_frame,
            bg=self.colors["bg"]
        )

        footer.pack(
            fill=tk.X,
            padx=36,
            pady=(0, 16),
        )

        self.history_prev_btn = self._make_button(
            footer,
            "‹ Anterior",
            self._prev_history_page,
            self.colors["button"],
            self.colors["button_hover"],
        )

        self.history_prev_btn.pack(side=tk.LEFT)

        self.history_page_label = tk.Label(
            footer,
            text="Pág 1 / 1",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 12),
        )

        self.history_page_label.pack(side=tk.RIGHT)

        self.history_next_btn = self._make_button(
            footer,
            "Siguiente ›",
            self._next_history_page,
            self.colors["button"],
            self.colors["button_hover"],
        )

        self.history_next_btn.pack(
            side=tk.RIGHT,
            padx=(0, 14),
        )

        self._render_history_entries()
    def load_from_history(self, pdf_path):
        """Cargar archivo directamente desde el historial"""
        if self.ui.is_reading:
            self.ui.lector.pause_reading()
        
        self.ui.pdf_path = pdf_path
        
        loading_win = tk.Toplevel(self.ui.root)
        loading_win.overrideredirect(True) 
        loading_win.configure(bg="#1e1e1e")

        width = 500
        height = 220

        screen_w = loading_win.winfo_screenwidth()
        screen_h = loading_win.winfo_screenheight()

        x = (screen_w // 2) - (width // 2)
        y = (screen_h // 2) - (height // 2)

        loading_win.geometry(f"{width}x{height}+{x}+{y}")

        loading_win.attributes("-alpha", 0.97)

        frame = tk.Frame(
            loading_win,
            bg="#1e1e1e",
            highlightthickness=1,
            highlightbackground="#333333"
        )
        frame.pack(fill="both", expand=True)

        title_label = tk.Label(
            frame,
            text="📄  Cargando archivo...",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        title_label.pack(pady=(25, 15))

        msg_label = tk.Label(
            frame,
            text="Cargando, por favor espere...",
            font=("Segoe UI", 16),
            fg="#dddddd",
            bg="#1e1e1e"
        )
        msg_label.pack(pady=(10, 25))

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor="#2b2b2b",
            bordercolor="#2b2b2b",
            background="#21f39a",
            lightcolor="#21f39a",
            darkcolor="#21f39a",
            thickness=18
        )

        pb = ttk.Progressbar(
            frame,
            style="Modern.Horizontal.TProgressbar",
            mode="indeterminate"
        )

        pb.pack(fill="x", padx=40, pady=10)
        pb.start(12)

        def load_in_thread():
            if pdf_path.lower().endswith(".pdf"):
                self.ui.pdf.load_pdf_text()
            elif pdf_path.lower().endswith(".txt"):
                self.ui.pdf.load_txt_text()
            pb.stop()
            loading_win.destroy()

            self.ui.historial.close_history_window()

            if pdf_path in self.ui.history:
                self.ui.root.after(10, self.ui.historial.show_resume_option)
            else:
                self.ui.current_block_index = 0
                self.ui.current_sentence_index = 0
                self.ui.lector.update_ui()


        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def delete_history_entry(self, pdf_path):
        """Eliminar entrada del historial"""
        confirm = messagebox.askyesno("Confirmar", 
            f"¿Eliminar '{os.path.basename(pdf_path)}' del historial?")
        
        if confirm:
            if pdf_path in self.ui.history:
                del self.ui.history[pdf_path]
                self.ui.pdf.save_history()
                
                if self.ui.history_window and self.ui.history_window.winfo_exists():
                    self.ui.history_window.destroy()
                    self.ui.history_window = None
                    self.ui.historial.show_history_window()
                
                if self.ui.pdf_path == pdf_path:
                    self.ui.saved_position_marker.config(text="")
    
    def edit_history_entry(self, pdf_path):
        """Permite editar la página en el historial."""
        edit_win = tk.Toplevel(self.ui.root)
        edit_win.title("Editar posición")
        edit_win.configure(bg=self.colors["bg"])
        edit_win.resizable(False, False)
        self._center_window(edit_win, 460, 260)

        current_pos = self.ui.history[pdf_path].get("position", 0) + 1
        total = self.ui.history[pdf_path].get("total_blocks", 0)

        filename = os.path.basename(pdf_path)
        max_chars = 52
        display_name = filename if len(filename) <= max_chars else filename[:max_chars - 1] + "…"

        tk.Label(
            edit_win,
            text=f"Editar posición: {display_name}",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
            wraplength=420, justify="center",
        ).pack(pady=(22, 6), padx=16)

        tk.Label(
            edit_win,
            text=f"Total de páginas/bloques: {total}",
            bg=self.colors["bg"], fg=self.colors["muted"],
            font=("Segoe UI", 10),
        ).pack(pady=(0, 14))

        input_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        input_frame.pack(pady=4)

        tk.Label(
            input_frame, text="Nueva posición:",
            bg=self.colors["bg"], fg=self.colors["text"],
            font=("Segoe UI", 11),
        ).pack(side=tk.LEFT, padx=(0, 10))
 
        spin_style = ttk.Style(edit_win)
        spin_style.configure(
            "Dark.TSpinbox",
            fieldbackground=self.colors["search"],
            background=self.colors["search"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["text"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
            insertcolor=self.colors["text"],
        )

        spinbox_var = tk.StringVar(value=str(current_pos))
        spinbox = ttk.Spinbox(
            input_frame,
            from_=1, to=total,
            textvariable=spinbox_var,
            width=8,
            font=("Segoe UI", 13),
            style="Dark.TSpinbox",
        )
        spinbox.pack(side=tk.LEFT, ipady=6)
        spinbox.focus_set()
        spinbox.selection_range(0, tk.END)

        def save_edit():
            try:
                new_pos = int(spinbox_var.get()) - 1
                if 0 <= new_pos < total:
                    self.ui.history[pdf_path]["position"] = new_pos
                    self.ui.history[pdf_path]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.ui.pdf.save_history()
                    if self.ui.pdf_path == pdf_path and self.ui.is_reading:
                        self.ui.lector.pause_reading()
                        self.ui.current_block_index = new_pos
                        self.ui.progress["value"] = new_pos
                        self.ui.lector.highlight_block(new_pos)
                        self.ui.lector.update_ui()
                        messagebox.showinfo(
                            "Información",
                            f"Posición actualizada a {new_pos + 1}. La lectura se ha pausado.",
                            parent=edit_win,
                        )
                    else:
                        messagebox.showinfo(
                            "Información", "Posición actualizada correctamente", parent=edit_win
                        )
                    edit_win.destroy()
                    if self.ui.history_window and self.ui.history_window.winfo_exists():
                        self._render_history_entries()
                else:
                    messagebox.showwarning(
                        "Error", f"El número debe estar entre 1 y {total}", parent=edit_win
                    )
            except ValueError:
                messagebox.showwarning("Error", "Ingrese un número válido", parent=edit_win)

        btn_frame = tk.Frame(edit_win, bg=self.colors["bg"])
        btn_frame.pack(pady=20)

        self._make_button(
            btn_frame, "✓  Guardar", save_edit,
            self.colors["green"], self.colors["green_hover"], width=12,
        ).pack(side=tk.LEFT, padx=10)
        self._make_button(
            btn_frame, "✕  Cancelar", edit_win.destroy,
            self.colors["red"], self.colors["red_hover"], width=12,
        ).pack(side=tk.LEFT, padx=10)

        edit_win.bind("<Return>", lambda _e: save_edit())
        edit_win.bind("<Escape>", lambda _e: edit_win.destroy())

    def close_history_window(self):
        """Cerrar ventana de historial y habilitar botón."""
        if self.ui.history_window:
            self.ui.history_window.destroy()
            self.ui.history_window = None
        self.ui.btn_view_history.config(state=tk.NORMAL)

    def show_resume_option(self):
        hist = self.ui.history[self.ui.pdf_path]

        BG       = "#1c1c2e"
        BG_CARD  = "#232336"
        FG_WHITE = "#e8e8f0"
        FG_DIM   = "#8888aa"
        FG_GREEN = "#00c2a0"
        C_GREEN  = "#16a979"
        C_GREEN_H= "#1dc48d"
        C_BLUE   = "#2979ff"
        C_BLUE_H = "#5090ff"

        resume_dialog = tk.Toplevel(self.ui.root)
        resume_dialog.title("Reanudar lectura")
        resume_dialog.configure(bg=BG)
        resume_dialog.resizable(False, False)
        self._center_window(resume_dialog, 500, 340)

        tk.Label(resume_dialog,
                text="¿Deseas reanudar la lectura de este archivo?",
                bg=BG, fg=FG_WHITE,
                font=("Segoe UI", 13)).pack(pady=(28, 10))

        pos_frame = tk.Frame(resume_dialog, bg=BG)
        pos_frame.pack()
        tk.Label(pos_frame, text="Posición guardada: ",
                bg=BG, fg=FG_WHITE,
                font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)
        tk.Label(pos_frame,
                text=f"{hist['position'] + 1}/{hist['total_blocks']}",
                bg=BG, fg=FG_GREEN,
                font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)

        tk.Label(resume_dialog,
                text=f"Última vez: {hist['timestamp']}",
                bg=BG, fg=FG_DIM,
                font=("Segoe UI", 10)).pack(pady=(4, 14))

        preview_outer = tk.Frame(resume_dialog, bg="#3a3a5c",
                                highlightthickness=1, highlightbackground="#3a3a5c")
        preview_outer.pack(padx=24, pady=(0, 18), fill=tk.X)

        preview = tk.Text(preview_outer, height=4, wrap=tk.WORD,
                        bg=BG_CARD, fg=FG_WHITE,
                        insertbackground=FG_WHITE,
                        relief=tk.FLAT, bd=0,
                        font=("Segoe UI", 10),
                        padx=14, pady=10)
        preview.pack(fill=tk.X)
        preview.insert(tk.END, hist.get("preview", "Sin vista previa"))
        preview.config(state=tk.DISABLED)

        btn_frame = tk.Frame(resume_dialog, bg=BG)
        btn_frame.pack(pady=(0, 24))

        def _make_pill(parent, text, command, bg, hover):
            btn = tk.Button(parent, text=text, command=command,
                            bg=bg, fg="white",
                            activebackground=hover, activeforeground="white",
                            relief=tk.FLAT, bd=0, cursor="hand2",
                            font=("Segoe UI", 11, "bold"),
                            padx=20, pady=10,
                            highlightthickness=0)
            btn.bind("<Enter>", lambda _e: btn.config(bg=hover))
            btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
            return btn

        _make_pill(btn_frame, "▷  Reanudar",
                lambda: self.resume_reading(hist["position"], resume_dialog),
                C_GREEN, C_GREEN_H).pack(side=tk.LEFT, padx=10)
        _make_pill(btn_frame, "↺  Comenzar de nuevo",
                lambda: self.resume_reading(0, resume_dialog),
                C_BLUE, C_BLUE_H).pack(side=tk.LEFT, padx=10)

    def resume_reading(self, position, dialog):
        """Reanudar lectura desde posición específica"""
        hist = self.ui.history.get(self.ui.pdf_path, {})
        self.ui.current_block_index = position
        
        self.ui.current_sentence_index = hist.get("sentence_index", 0)
        
        self.ui.lector.highlight_block(self.ui.current_block_index)
        self.ui.progress['value'] = self.ui.current_block_index
        self.ui.lector.update_ui()
        
        if dialog:
            dialog.destroy()
        
        if not self.ui.is_reading:
            self.ui.lector.start_reading()
        
        self.ui.btn_read.config(state=tk.NORMAL if self.ui.engine and self.ui.pdf_path else tk.DISABLED)

    def clear_history(self):
        """Borrar el historial de lecturas"""
        confirm = messagebox.askyesno(
            "Confirmar", 
            "¿Estás seguro de que deseas borrar todo el historial de lecturas?"
        )
        if confirm:
            self.ui.history = {}
            self.ui.pdf.save_history()
            self.ui.saved_position_marker.config(text="")
            messagebox.showinfo("Información", "El historial ha sido borrado.")

    def highlight_saved_position(self, position):
        """Resaltar la posición guardada en el texto"""
        self.ui.text_display.tag_remove('saved', 1.0, tk.END)
        
        if 0 <= position < len(self.ui.text_blocks):
            block = self.ui.text_blocks[position]
            start_pos = self.ui.text_display.search(
                block, 
                1.0, 
                tk.END, 
                nocase=True, 
                exact=True
            )
            
            if start_pos:
                end_pos = f"{start_pos}+{len(block)}c"
                self.ui.text_display.tag_add('saved', start_pos, end_pos)