from pathlib import Path

class Config:
    DEFAULT_MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"
    TEMP_DIR = Path("temp")
    
    MODELS = {
        'hppnet': {
            'exe': r"Audio2MIDI\transcribe.exe",
            'model': r"Audio2MIDI\model_audio2midi.pt"
        },
        'midi2score': {
            'exe': r"MIDI2MusicXML/interference.exe",
            'model': r"MIDI2MusicXML\MIDI2ScoreTF.ckpt"
        }
    }