import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from deeprhythm import DeepRhythmPredictor

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio to Score Transcription")
        
        # Ścieżki do środowisk i skryptów
        self.hppnet_python = r"C:\Users\krzyw\Source\Repos\HPPNet\hppvenv\Scripts\python.exe"
        self.midi2score_python = r"C:\Users\krzyw\Source\Repos\MIDI2ScoreTransformer\midi2scoreEnv\Scripts\python.exe"
        
        self.hppnet_script = r"C:\Users\krzyw\Source\Repos\HPPNet\transcribe.py"
        self.midi2score_script = r"C:\Users\krzyw\Source\Repos\MIDI2ScoreTransformer\midi2scoretransformer\evaluation\interference.py"
        
        # Ścieżki do modeli
        self.hppnet_model = r"C:\Users\krzyw\Desktop\inz\Hppnet_wytrenowane\model_base-81600.pt"
        self.midi2score_model = r"C:\Users\krzyw\Desktop\inz\Testy_midi2score\MIDI2ScoreTF.ckpt"
        
        #Ścieżka do MuseScore
        self.musescore_path = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
        # Utwórz folder na pliki tymczasowe
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)
        
        self.create_gui()
    
    def create_gui(self):
        # Frame na wybór pliku audio
        input_frame = ttk.LabelFrame(self.root, text="Input", padding="10")
        input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        self.input_path = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.input_path, width=50).grid(row=0, column=0, padx=5)
        self.input_browse_btn = ttk.Button(input_frame, text="Browse Audio", command=self.browse_input)
        self.input_browse_btn.grid(row=0, column=1, padx=5)
        
        # Frame na wybór folderu wyjściowego
        output_frame = ttk.LabelFrame(self.root, text="Output", padding="10")
        output_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        self.output_path = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_path, width=50).grid(row=0, column=0, padx=5)
        self.output_browse_btn = ttk.Button(output_frame, text="Browse Output", command=self.browse_output)
        self.output_browse_btn.grid(row=0, column=1, padx=5)
        
        # Status i Progress Bar
        status_frame = ttk.LabelFrame(self.root, text="Progress", padding="10")
        status_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        
        self.progress = ttk.Progressbar(status_frame, length=400, mode='determinate')
        self.progress.grid(row=0, column=0, padx=5, pady=5)
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, padx=5)
        
        # Log window
        log_frame = ttk.LabelFrame(self.root, text="Log", padding="10")
        log_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        
        self.log_text = tk.Text(log_frame, height=10, width=60)
        self.log_text.grid(row=0, column=0, padx=5, pady=5)
        
        # Przycisk do uruchomienia transkrypcji
        self.transcription_btn = ttk.Button(self.root, text="Start Transcription", command=self.start_transcription_thread)
        self.transcription_btn.grid(row=4, column=0, pady=10)
        
        # Frame na wybór ścieżki do MuseScore
        musescore_frame = ttk.LabelFrame(self.root, text="MuseScore Path", padding="10")
        musescore_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")

        self.musescore_path_var = tk.StringVar(value=self.musescore_path)
        ttk.Entry(musescore_frame, textvariable=self.musescore_path_var, width=50).grid(row=0, column=0, padx=5)
        self.musescore_browse_btn = ttk.Button(musescore_frame, text="Browse MuseScore", command=self.browse_musescore)
        self.musescore_browse_btn.grid(row=0, column=1, padx=5)
    
    def browse_musescore(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("MuseScore Executable", "*.exe")],
            title="Select MuseScore Executable"
        )
        if filepath:
            self.musescore_path_var.set(filepath)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3")]
        )
        if filename:
            self.input_path.set(filename)

    def toggle_buttons(self, state):
        self.input_browse_btn.config(state=state)
        self.output_browse_btn.config(state=state)
        self.transcription_btn.config(state=state)
        
    def browse_output(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_path.set(directory)
    
    def start_transcription_thread(self):
        """Uruchamia run_transcription w osobnym wątku."""
        self.toggle_buttons("disabled")
        threading.Thread(target=self.run_transcription, daemon=True).start()

    def predict_bpm(self, file):
        model = DeepRhythmPredictor()
        tempo, _ = model.predict(file, include_confidence=True)
        return tempo

    def add_tempo_to_musicxml(self, musicxml_path, tempo):
        tree = ET.parse(musicxml_path)
        root = tree.getroot()

        # Znajdź pierwszy `<measure>` wewnątrz `<part>`
        measure = root.find(".//part/measure")
        if measure is None:
            raise ValueError("Invalid MusicXML: No <measure> element found.")

        # Tworzenie elementu <direction> dla tempa
        direction = ET.Element("direction", placement="above")
        direction_type = ET.SubElement(direction, "direction-type")
        metronome = ET.SubElement(direction_type, "metronome")
        
        beat_unit = ET.SubElement(metronome, "beat-unit")
        beat_unit.text = "quarter"  # Domyślnie ćwierćnuty
        per_minute = ET.SubElement(metronome, "per-minute")
        per_minute.text = str(tempo)  # Tempo w BPM

        # Dodanie elementu <direction> na początku `<measure>`
        measure.insert(0, direction)

        # Zapisz zmodyfikowany plik MusicXML
        tree.write(musicxml_path)

    def run_transcription(self):
        if not self.input_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Please select input file and output location")
            return
        
        try:
            midi_path = self.temp_dir / "temp.mid"
            output_xml = Path(self.output_path.get()) / f"{Path(self.input_path.get()).stem}.musicxml"
            output_pdf = Path(self.output_path.get()) / f"{Path(self.input_path.get()).stem}.pdf"

            # Krok 1: HPPNet (Audio -> MIDI)
            self.status_var.set("Converting audio to MIDI...")
            self.progress['value'] = 25
            self.root.update()
            
            self.log(f"Running HPPNet on {self.input_path.get()}")
            process = subprocess.run([
                self.hppnet_python,
                self.hppnet_script,
                "--flac_paths", self.input_path.get(),
                "--model_file", self.hppnet_model,
                "--save-path", str(midi_path)
            ], capture_output=True, text=True, check=True)
            
            if process.returncode != 0:
                self.log(f"Error output: {process.stderr}")
                raise Exception(f"Audio to MIDI conversion failed: {process.stderr}")
            self.log(process.stdout)

            # Krok 2: Wykrywanie tempa
            self.status_var.set("Detecting tempo...")
            self.progress['value'] = 50
            self.root.update()
            
            self.log(f"Detecting tempo from {self.input_path.get()}")
            tempo = self.predict_bpm(self.input_path.get())
            self.log(f"Detected tempo: {tempo} BPM")
            
            # Krok 3: MIDI2Score (MIDI -> MusicXML)
            self.status_var.set("Converting MIDI to MusicXML...")
            self.progress['value'] = 75
            self.root.update()
            
            self.log(f"Running MIDI2Score on {midi_path}")
            process = subprocess.run([
                self.midi2score_python,
                self.midi2score_script,
                "--midi_path", str(midi_path),
                "--model_checkpoint", self.midi2score_model,
                "--output_xml_path", str(output_xml)
            ], capture_output=True, text=True, check=True)
            
            if process.returncode != 0:
                self.log(f"Error output: {process.stderr}")
                raise Exception(f"MIDI to MusicXML conversion failed: {process.stderr}")
            self.log(process.stdout)

            # Krok 4: Dodanie tempa do MusicXML
            self.status_var.set("Adding tempo to MusicXML...")
            self.log(f"Adding detected tempo ({tempo} BPM) to {output_xml}")
            self.add_tempo_to_musicxml(output_xml, tempo)

            # Krok 5: MusicXML -> PDF
            self.status_var.set("Generating sheet music PDF...")
            self.progress['value'] = 100
            self.root.update()
            
            self.log(f"Running MuseScore to generate PDF from {output_xml}")
            command = [
                self.musescore_path,
                "-o", str(output_pdf),
                str(output_xml)
            ]
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            
            if process.returncode != 0:
                self.log(f"Error output: {process.stderr}")
                raise Exception(f"MusicXML to PDF conversion failed: {process.stderr}")
            self.log(process.stdout)

            self.status_var.set("Transcription completed successfully!")
            messagebox.showinfo("Success", f"Transcription and PDF saved to:\n{output_xml}\n{output_pdf}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error occurred during transcription")
        finally:
            if midi_path.exists():
                midi_path.unlink()
            self.progress['value'] = 0
            self.toggle_buttons("normal")



def main():
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()