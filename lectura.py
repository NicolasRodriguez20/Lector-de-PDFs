import threading
import time
import keyboard
import tkinter as tk 
from tkinter import messagebox
from pdfs import Pdfs
class Lectura:
    def __init__(self, ui):
        self.ui = ui
        self.current_sentence_index = 0  # Siempre en self, nunca en self.ui
        keyboard.add_hotkey('f7', self._hotkey_toggle)
    def _hotkey_toggle(self):
        self.ui.root.after(0, self.toggle_reading)

    def pause_reading(self):
        """Pausar la lectura (sin matar el hilo)"""
        self.ui.is_reading = False
        self.ui.btn_read.config(text="Continuar")
        self.ui.btn_select.config(state=tk.NORMAL)
        if self.ui.engine:
            self.ui.engine.stop()
        self.ui.btn_prev.config(state=tk.NORMAL)
        self.ui.btn_next.config(state=tk.NORMAL)
        if not self.ui.pdf_path:
            self.ui.pdf.guardar_historial_manual()
        self.ui.pdf.update_history()

    def start_reading(self):
        """Iniciar lectura continua en un único hilo"""
        if not self.ui.text_blocks or not self.ui.engine:
            return
        if hasattr(self, "reading_thread") and self.reading_thread.is_alive():
            self.ui.is_reading = True
            self.ui.btn_read.config(text="Pausar")
            self.ui.btn_select.config(state=tk.DISABLED)
            return
        self.ui.is_reading = True
        self.ui.btn_read.config(text="Pausar")
        self.ui.btn_select.config(state=tk.DISABLED)
        self.ui.btn_prev.config(state=tk.DISABLED)
        self.ui.btn_next.config(state=tk.DISABLED)
        self.reading_thread = threading.Thread(target=self.read_continuous, daemon=True)
        self.reading_thread.start()

    def read_continuous(self):
        while self.ui.current_block_index < len(self.ui.text_blocks):
            if not self.ui.is_reading:
                time.sleep(0.05)
                continue
            block = self.ui.text_blocks[self.ui.current_block_index]
            sentences = [s.strip() for s in block.replace("\n", " ").split(". ") if s.strip()]
            while self.current_sentence_index < len(sentences):
                if not self.ui.is_reading:
                    break
                sentence = sentences[self.current_sentence_index]
                self.ui.root.after(0, lambda i=self.ui.current_block_index: self.highlight_block(i))
                self.ui.engine.say(sentence)
                if not self.ui.is_reading:
                    break
                self.current_sentence_index += 1
            if self.current_sentence_index >= len(sentences) and self.ui.is_reading:
                self.current_sentence_index = 0
                self.ui.current_block_index += 1
                self.ui.progress['value'] = self.ui.current_block_index
                self.ui.root.after(0, self.update_ui)
            else:
                break
        if self.ui.current_block_index >= len(self.ui.text_blocks):
            self.ui.root.after(0, self._on_reading_finished)
    def _on_reading_finished(self):
        """Llamado desde el hilo principal cuando se termina de leer todo"""
        self.ui.btn_select.config(state=tk.NORMAL)
        self.ui.btn_prev.config(state=tk.NORMAL)
        self.ui.btn_next.config(state=tk.NORMAL)
        self.ui.is_reading = False
        self.ui.btn_read.config(text="Leer")
        self.current_sentence_index = 0

    def stop_reading(self):
        """Detener completamente la lectura y reiniciar posición"""
        self.ui.is_reading = False
        self.ui.current_block_index = 0
        self.current_sentence_index = 0
        self.ui.progress['value'] = 0
        if self.ui.engine:
            self.ui.engine.stop()
        self.ui.btn_read.config(
            text="Leer",
            state=tk.NORMAL if self.ui.engine and self.ui.pdf_path else tk.DISABLED
        )
        self.ui.btn_select.config(state=tk.NORMAL)
        self.ui.btn_prev.config(state=tk.NORMAL)
        self.ui.btn_next.config(state=tk.NORMAL)
        self.ui.text_display.tag_remove('highlight', 1.0, tk.END)
        self.update_ui()

    def update_ui(self):
        """Actualizar todos los elementos de la interfaz"""
        total = len(self.ui.text_blocks)
        current = self.ui.current_block_index + 1 if total > 0 else 0
        self.ui.block_counter.config(text=f"{current}/{total}")
        if self.ui.pdf_path in self.ui.history:
            saved_pos = self.ui.history[self.ui.pdf_path]['position']
            self.ui.saved_position_marker.config(
                text=f"Guardado: {saved_pos + 1}/{total}",
                fg="green"
            )
            self.ui.historial.highlight_saved_position(saved_pos)
        else:
            self.ui.saved_position_marker.config(text="")
    def highlight_block(self, block_index):
        """Resaltar un bloque específico en el área de texto"""
        if 0 <= block_index < len(self.ui.text_blocks):
            block = self.ui.text_blocks[block_index]
            start_pos = self.ui.text_display.search(
                block,
                1.0,
                tk.END,
                nocase=True,
                exact=True
            )
            if start_pos:
                end_pos = f"{start_pos}+{len(block)}c"
                self.ui.text_display.tag_remove('highlight', 1.0, tk.END)
                self.ui.text_display.tag_add('highlight', start_pos, end_pos)
                self.ui.text_display.see(start_pos)

    def toggle_reading(self):
        """Alternar entre lectura y pausa"""
        if not self.ui.is_reading:
            self.start_reading()
        else:
            self.pause_reading()
    def toggle_speed(self):
        """Alternar entre velocidad normal y rápida"""
        if self.ui.engine:
            if self.ui.current_speed == self.ui.normal_speed:
                self.ui.current_speed = self.ui.fast_speed
                self.ui.btn_speed.config(text="Velocidad: 2x", bg="#FF5722")
            else:
                self.ui.current_speed = self.ui.normal_speed
                self.ui.btn_speed.config(text="Velocidad: 1x", bg="#2196F3")
            self.ui.engine.setProperty('rate', self.ui.current_speed)
    def previous_block(self):
        """Retroceder un bloque (solo si está pausado)"""
        if not self.ui.is_reading and self.ui.current_block_index > 0:
            self.ui.current_block_index -= 1
            self.current_sentence_index = 0 
            self.ui.progress['value'] = self.ui.current_block_index
            self.highlight_block(self.ui.current_block_index)
            self.update_ui()
    def next_block(self):
        """Avanzar un bloque (solo si está pausado)"""
        if not self.ui.is_reading and self.ui.current_block_index < len(self.ui.text_blocks) - 1:
            self.ui.current_block_index += 1
            self.current_sentence_index = 0  
            self.ui.progress['value'] = self.ui.current_block_index
            self.highlight_block(self.ui.current_block_index)
            self.update_ui()
    def terminar_lectura(self):
        confirm = messagebox.askyesno(
            "Confirmar",
            "¿Estás seguro de terminar la lectura? Se borrará el contenido actual."
        )
        if confirm:
            self.stop_reading()
            self.ui.text_display.delete(1.0, tk.END)
            self.ui.text_blocks = []
            self.ui.original_text_blocks = []
            self.ui.pdf_path = ""
            self.ui.current_block_index = 0
            self.current_sentence_index = 0
            self.ui.progress['value'] = 0
            self.ui.progress['maximum'] = 0
            self.ui.btn_read.config(state=tk.DISABLED, text="Leer")
            self.update_ui()
    def on_text_modified(self, event=None):
        """Manejador cuando se modifica el texto en el área de visualización"""
        current_text = self.ui.text_display.get(1.0, tk.END).strip()
        if not self.ui.pdf_path:
            if current_text:
                self.ui.text_blocks = [block for block in current_text.split('\n\n') if block.strip()]
                self.ui.progress['maximum'] = len(self.ui.text_blocks)
                self.ui.current_block_index = 0
                self.ui.btn_read.config(state=tk.NORMAL if self.ui.engine else tk.DISABLED)
            else:
                self.ui.text_blocks = []
                self.ui.progress['maximum'] = 0
                self.ui.progress['value'] = 0
                self.ui.btn_read.config(state=tk.DISABLED)
            return
        if self.ui.pdf_path:
            new_blocks = [block for block in current_text.split('\n\n') if block.strip()]
            if new_blocks != self.ui.text_blocks:
                if self.ui.is_reading:
                    self.pause_reading()
                    messagebox.showinfo("Información", "La lectura se ha pausado porque el texto fue modificado.")
                self.ui.text_blocks = new_blocks
                self.ui.progress['maximum'] = len(self.ui.text_blocks)
                if self.ui.current_block_index >= len(self.ui.text_blocks):
                    self.ui.current_block_index = max(0, len(self.ui.text_blocks) - 1)
                self.ui.progress['value'] = self.ui.current_block_index
                self.update_ui()
    def on_closing(self):
        """Manejador para cuando se cierra la ventana"""
        self.ui.pdf.update_history()
        self.ui.root.destroy()
