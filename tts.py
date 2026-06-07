import asyncio
import threading
import os
import tempfile
import pygame 
import edge_tts
import pyttsx3
class Pyttsx3Voice:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.is_speaking = False
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id)  
    def say(self, text):
        if not text.strip():
            return
        self.is_speaking = True
        self.engine.say(text)
        self.engine.runAndWait()
        self.is_speaking = False
    def stop(self):
        self.engine.stop()
        self.is_speaking = False
    def setProperty(self, prop, value):
        if prop == "rate":
            self.engine.setProperty('rate', value)
class EdgeTTSVoice:
    def __init__(self):
    
        self.voice = "es-ES-ElviraNeural"
        self.rate = "+0%"         
        self.normal_rate = "+0%"
        self.fast_rate = "+50%"    
        self.is_speaking = False
        self._stop_event = threading.Event()
        self._done_event = threading.Event()
        self._done_event.set()  
        self._pygame_init = False

    def say(self, text: str):
        if not text.strip():
            return
        self._done_event.wait()
        self._stop_event.clear()
        self._done_event.clear()
        self.is_speaking = True
        t = threading.Thread(target=self._speak_worker, args=(text,), daemon=True)
        t.start()
        self._done_event.wait()

    def _speak_worker(self, text: str):
        try:
            print(f"Generando: '{text[:80]}...' | rate={self.rate} | voz={self.voice}")
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            asyncio.run(communicate.save(tmp_path))
            if self._stop_event.is_set():
                return
            if not self._pygame_init:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                self._pygame_init = True
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    break
                pygame.time.wait(100)
        except Exception as e:
            print(f"Error en reproducción: {e}")
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            self.is_speaking = False
            self._done_event.set()

    def stop(self):
        self._stop_event.set()          
        if self._pygame_init:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self.is_speaking = False
        self._done_event.set()        
    def setProperty(self, prop, value):
        if prop == "rate":
            if value <= 150:
                self.rate = self.normal_rate
            else:
                percent = min(50, int((value - 150) / 3)) 
                self.rate = f"+{percent}%"
