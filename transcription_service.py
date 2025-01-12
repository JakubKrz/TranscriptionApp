import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from deeprhythm import DeepRhythmPredictor
from config import Config
from typing import Optional

class TranscriptionError(Exception):
    pass

class TranscriptionService:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback
        self.temp_dir = Config.TEMP_DIR
        self.temp_dir.mkdir(exist_ok=True)

    def update_status(self, message: str, progress: int):
        if self.status_callback:
            self.status_callback(message, progress)

    def predict_bpm(self, file_path: str) -> float:
        model = DeepRhythmPredictor()
        tempo, _ = model.predict(file_path, include_confidence=True)
        return tempo

    def add_tempo_to_musicxml(self, musicxml_path: Path, tempo: float):
        tree = ET.parse(musicxml_path)
        root = tree.getroot()
        
        measure = root.find(".//part/measure")
        if measure is None:
            raise TranscriptionError("Invalid MusicXML: No <measure> element found.")
            
        direction = ET.Element("direction", placement="above")
        direction_type = ET.SubElement(direction, "direction-type")
        metronome = ET.SubElement(direction_type, "metronome")
        
        beat_unit = ET.SubElement(metronome, "beat-unit")
        beat_unit.text = "quarter"
        per_minute = ET.SubElement(metronome, "per-minute")
        per_minute.text = str(tempo)
        
        measure.insert(0, direction)
        tree.write(musicxml_path)

    def run_subprocess(self, command: list, error_message: str) -> str:
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=True)
            return process.stdout
        except subprocess.CalledProcessError as e:
            raise TranscriptionError(f"{error_message}: {e.stderr}")

    def transcribe(self, input_path: Path, output_dir: Path, musescore_path: Optional[Path] = None) -> tuple[Path, Path]:
        midi_path = self.temp_dir / "temp.mid"
        output_xml = output_dir / f"{input_path.stem}.musicxml"
        output_pdf = output_dir / f"{input_path.stem}.pdf"

        try:
            # Audio to MIDI
            self.update_status("Converting audio to MIDI...", 25)
            self.run_subprocess([
                Config.MODELS['hppnet']['exe'],
                "--flac_paths", str(input_path),
                "--model_file", Config.MODELS['hppnet']['model'],
                "--save-path", str(midi_path)
            ], "Audio to MIDI conversion failed")

            # Tempo detection
            self.update_status("Detecting tempo...", 50)
            tempo = self.predict_bpm(str(input_path))

            # MIDI to MusicXML
            self.update_status("Converting MIDI to MusicXML...", 75)
            self.run_subprocess([
                Config.MODELS['midi2score']['exe'],
                "--midi_path", str(midi_path),
                "--model_checkpoint", Config.MODELS['midi2score']['model'],
                "--output_xml_path", str(output_xml)
            ], "MIDI to MusicXML conversion failed")

            # Add tempo to MusicXML
            self.update_status("Adding tempo to MusicXML...", 90)
            self.add_tempo_to_musicxml(output_xml, tempo)

            # Generate PDF if MuseScore path is provided
            if musescore_path:
                self.update_status("Generating sheet music PDF...", 95)
                self.run_subprocess([
                    str(musescore_path),
                    "-o", str(output_pdf),
                    str(output_xml)
                ], "PDF generation failed")

            self.update_status("Transcription completed successfully!", 100)
            return output_xml, output_pdf

        finally:
            if midi_path.exists():
                midi_path.unlink()