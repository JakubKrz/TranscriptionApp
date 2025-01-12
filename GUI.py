import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from transcription_service import TranscriptionService, TranscriptionError
from config import Config

class TranscriptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio to Score Transcription")
        self.setup_variables()
        self.create_gui()
        self.transcription_service = TranscriptionService(self.update_status)

    def setup_variables(self):
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.musescore_path_var = tk.StringVar(value=Config.DEFAULT_MUSESCORE_PATH)
        self.status_var = tk.StringVar(value="Ready")

    def update_status(self, message: str, progress: int):
        self.status_var.set(message)
        self.progress['value'] = progress
        self.log(message)
        self.root.update()

    def create_gui(self):
        self.create_input_frame()
        self.create_output_frame()
        self.create_status_frame()
        self.create_log_frame()
        self.create_transcription_button()
        self.create_musescore_frame()

    def create_input_frame(self):
        frame = self.create_labeled_frame("Input", 0)
        self.create_path_selector(frame, self.input_path, "Browse Audio", 
                                self.browse_input, filetypes=[("Audio Files", "*.wav *.mp3")])

    def create_output_frame(self):
        frame = self.create_labeled_frame("Output", 1)
        self.create_path_selector(frame, self.output_path, "Browse Output", 
                                self.browse_output, is_directory=True)

    def create_status_frame(self):
        frame = self.create_labeled_frame("Progress", 2)
        self.progress = ttk.Progressbar(frame, length=400, mode='determinate')
        self.progress.grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(frame, textvariable=self.status_var).grid(row=1, column=0, padx=5)

    def create_log_frame(self):
        frame = self.create_labeled_frame("Log", 3)
        self.log_text = tk.Text(frame, height=10, width=60)
        self.log_text.grid(row=0, column=0, padx=5, pady=5)

    def create_musescore_frame(self):
        frame = self.create_labeled_frame("MuseScore Path", 5)
        self.create_path_selector(frame, self.musescore_path_var, "Browse MuseScore", 
                                self.browse_musescore, filetypes=[("MuseScore Executable", "*.exe")])

    def create_labeled_frame(self, text: str, row: int) -> ttk.LabelFrame:
        frame = ttk.LabelFrame(self.root, text=text, padding="10")
        frame.grid(row=row, column=0, padx=10, pady=5, sticky="ew")
        return frame

    def create_path_selector(self, parent, variable, button_text, command, 
                           filetypes=None, is_directory=False):
        ttk.Entry(parent, textvariable=variable, width=50).grid(row=0, column=0, padx=5)
        btn = ttk.Button(parent, text=button_text, command=command)
        btn.grid(row=0, column=1, padx=5)
        return btn

    def create_transcription_button(self):
        self.transcription_btn = ttk.Button(self.root, text="Start Transcription", 
                                          command=self.start_transcription_thread)
        self.transcription_btn.grid(row=4, column=0, pady=10)

    def browse_input(self):
        self.browse_file(self.input_path, [("Audio Files", "*.wav *.mp3")])

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path.set(path)

    def browse_musescore(self):
        self.browse_file(self.musescore_path_var, [("MuseScore Executable", "*.exe")])

    def browse_file(self, variable, filetypes):
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            variable.set(filename)

    def log(self, message: str):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

    def toggle_buttons(self, state: str):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.config(state=state)

    def start_transcription_thread(self):
        if not self.input_path.get() or not self.output_path.get():
            messagebox.showerror("Error", "Please select input file and output location")
            return
        
        self.toggle_buttons("disabled")
        threading.Thread(target=self.run_transcription, daemon=True).start()

    def run_transcription(self):
        try:
            output_xml, output_pdf = self.transcription_service.transcribe(
                Path(self.input_path.get()),
                Path(self.output_path.get()),
                Path(self.musescore_path_var.get())
            )
            messagebox.showinfo("Success", 
                              f"MusicXML and PDF saved to:\n{output_xml}\n{output_pdf}")
        except TranscriptionError as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Error occurred during transcription")
        finally:
            self.progress['value'] = 0
            self.toggle_buttons("normal")

# main.py
def main():
    root = tk.Tk()
    app = TranscriptionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()