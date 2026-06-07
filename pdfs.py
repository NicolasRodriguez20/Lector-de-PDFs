import json
import os
import PyPDF2
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
from datetime import datetime
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\casatres\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

from pathlib import Path

class Pdfs:
    def __init__(self, ui):
        self.ui = ui


    def guardar_historial_manual(self):
        BG       = "#0f0f1a"
        FG       = "#e8e8f0"
        FG_DIM   = "#7a7a9a"
        ENTRY_BG = "#1a1a2e"
        FOCUS_BD = "#3a8fff"
        C_GREEN  = "#2e7d4f"
        C_GREEN_H= "#3a9e63"
        C_RED    = "#8b2020"
        C_RED_H  = "#aa2a2a"

        top = tk.Toplevel(self.ui.root)
        top.title("Guardar historial")
        top.configure(bg=BG)
        top.resizable(False, False)

        w, h = 420, 260
        top.update_idletasks()
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        top.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        tk.Label(top, text="Nombre para el historial:",
                bg=BG, fg=FG,
                font=("Segoe UI", 15, "bold")).pack(pady=(36, 18))

        entry_outer = tk.Frame(top, bg=FG_DIM,  
                            highlightthickness=0)
        entry_outer.pack(padx=36, fill=tk.X)

        entry = tk.Entry(entry_outer,
                        bg=ENTRY_BG, fg=FG,
                        insertbackground=FG,
                        relief=tk.FLAT, bd=0,
                        font=("Segoe UI", 13),
                        highlightthickness=2,
                        highlightbackground=FG_DIM,
                        highlightcolor=FOCUS_BD)
        entry.pack(fill=tk.X, ipady=10, padx=2, pady=2)
        entry.focus_set()

        btn_frame = tk.Frame(top, bg=BG)
        btn_frame.pack(pady=24)

        def _btn(parent, text, command, bg, hover):
            b = tk.Button(parent, text=text, command=command,
                        bg=bg, fg=FG,
                        activebackground=hover, activeforeground=FG,
                        relief=tk.FLAT, bd=0, cursor="hand2",
                        font=("Segoe UI", 11, "bold"),
                        padx=20, pady=10,
                        highlightthickness=0)
            b.bind("<Enter>", lambda _e: b.config(bg=hover))
            b.bind("<Leave>", lambda _e: b.config(bg=bg))
            return b

        def guardar():
            nombre = entry.get().strip()
            if not nombre:
                messagebox.showwarning("Aviso", "Debes ingresar un nombre.", parent=top)
                return
            documents_path = Path.home() / "Documents" / "Historial"
            documents_path.mkdir(parents=True, exist_ok=True)
            ruta = documents_path / f"{nombre}.txt"
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.ui.text_display.get(1.0, tk.END))
            messagebox.showinfo("Éxito", f"Historial guardado en:\n{ruta}", parent=top)
            self.ui.btn_read.config(state=tk.NORMAL)
            top.destroy()

        _btn(btn_frame, "✓  Guardar", guardar, C_GREEN, C_GREEN_H).pack(side=tk.LEFT, padx=10)
        _btn(btn_frame, "✕  Cancelar", top.destroy, C_RED, C_RED_H).pack(side=tk.LEFT, padx=10)

        top.bind("<Return>", lambda _e: guardar())
        top.bind("<Escape>", lambda _e: top.destroy())

    def update_history(self):
        """Actualizar historial con la posición actual"""
        if self.ui.pdf_path and self.ui.text_blocks:
            self.ui.history[self.ui.pdf_path] = {
                'position': self.ui.current_block_index,
                'sentence_index': getattr(self.ui, "current_sentence_index", 0), 
                'total_blocks': len(self.ui.text_blocks),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'preview': self.ui.text_blocks[self.ui.current_block_index][:100] + "..."
                if self.ui.current_block_index < len(self.ui.text_blocks) else ""
            }
            self.save_history()
    
    def save_history(self):
        """Guardar historial a archivo JSON"""
        try:
            with open(self.ui.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.ui.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando historial: {e}")
    
    def load_pdf_text(self):
        """Cargar y mostrar el texto del PDF con mejor manejo de formatos complejos"""

        self.ui.text_display.delete(1.0, tk.END)

        self.ui.text_blocks = []
        self.ui.current_block_index = 0

        try:
            with open(self.ui.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                full_text = ""
                
                for page in reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            cleaned_text = ' '.join(page_text.replace('\n', ' ').split())
                            full_text += cleaned_text + "\n\n"
                    except Exception as e:
                        print(f"Error extrayendo texto de página: {e}")
                        continue
                
                if not full_text.strip():
                    messagebox.showwarning(
                        "Advertencia",
                        "No se pudo extraer texto del PDF. Puede ser escaneado o protegido."
                    )
                    full_text = "No se pudo extraer texto de este archivo PDF."

                self.ui.original_text_blocks = [
                    block for block in full_text.split('\n\n') if block.strip()
                ]

                self.ui.text_blocks = self.ui.original_text_blocks.copy()

                self.ui.text_display.insert(tk.END, full_text)

                self.ui.progress['maximum'] = len(self.ui.text_blocks)
                self.ui.progress['value'] = 0

                self.ui.btn_read.config(
                    state=tk.NORMAL if self.ui.engine and self.ui.text_blocks else tk.DISABLED
                )

                self.ui.lector.update_ui()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el PDF: {str(e)}")
            self.ui.text_display.insert(tk.END, f"Error al cargar el PDF: {str(e)}")
    
    def load_txt_text(self):
        """Cargar y mostrar el texto de un archivo TXT"""

        self.ui.text_display.delete(1.0, tk.END)

        self.ui.text_blocks = []
        self.ui.current_block_index = 0

        try:
            with open(self.ui.pdf_path, 'r', encoding='utf-8') as file:
                full_text = file.read()

            self.ui.original_text_blocks = [
                block for block in full_text.split('\n\n') if block.strip()
            ]
            self.ui.text_blocks = self.ui.original_text_blocks.copy()

            self.ui.text_display.insert(tk.END, full_text)

            self.ui.progress['maximum'] = len(self.ui.text_blocks)
            self.ui.progress['value'] = 0

            self.ui.btn_read.config(
                state=tk.NORMAL if self.ui.engine and self.ui.text_blocks else tk.DISABLED
            )

            self.ui.lector.update_ui()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el TXT: {str(e)}")
            self.ui.text_display.insert(tk.END, f"Error al cargar el TXT: {str(e)}")

    def load_history(self):
        """Cargar historial desde archivo JSON"""
        if os.path.exists(self.ui.HISTORY_FILE):
            try:
                with open(self.ui.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando historial: {e}")
                return {}
        return {}
    def select_pdf(self):
        """Seleccionar archivo PDF y cargar historial si existe"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        
        if file_path:
            self.ui.pdf.update_history()
            self.ui.pdf_path = file_path
            
            loading_win = tk.Toplevel(self.ui.root)
            loading_win.title("Cargando PDF...")
            loading_win.geometry("300x100")
            loading_win.resizable(False, False)
            tk.Label(loading_win, text="Cargando, por favor espere...").pack(pady=10)
            pb = ttk.Progressbar(loading_win, mode='indeterminate')
            pb.pack(fill='x', padx=20, pady=10)
            pb.start(10)

            def load_in_thread():
                self.ui.pdf.load_pdf_text()
                pb.stop()
                loading_win.destroy()

                if file_path in self.ui.history:
                    self.ui.historial.show_resume_option()
                else:
                    self.ui.current_block_index = 0
                    self.ui.lector.update_ui()

            threading.Thread(target=load_in_thread, daemon=True).start()
    def select_file(self):
        """Seleccionar archivo PDF o TXT y cargar historial si existe"""
        if self.ui.is_reading:
            self.ui.lector.pause_reading()
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("PDF o TXT", "*.pdf *.txt"), ("PDF Files", "*.pdf"), ("Text Files", "*.txt")]
        )
        
        if file_path:
            self.ui.pdf.update_history()
            self.ui.pdf_path = file_path

            loading_win = tk.Toplevel(self.ui.root)
            loading_win.title("Cargando archivo...")
            loading_win.geometry("300x100")
            loading_win.resizable(False, False)
            tk.Label(loading_win, text="Cargando, por favor espere...").pack(pady=10)
            pb = ttk.Progressbar(loading_win, mode='indeterminate')
            pb.pack(fill='x', padx=20, pady=10)
            pb.start(10)

            def load_in_thread():
                if file_path.lower().endswith(".pdf"):
                    self.ui.pdf.load_pdf_text()
                elif file_path.lower().endswith(".txt"):
                    self.ui.pdf.load_txt_text()
                pb.stop()
                loading_win.destroy()

                if file_path in self.ui.history:
                    self.ui.historial.show_resume_option()
                else:
                    self.ui.current_block_index = 0
                    self.ui.lector.update_ui()

            threading.Thread(target=load_in_thread, daemon=True).start()
