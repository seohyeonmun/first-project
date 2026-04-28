from src.wakeword import run
from src.stt import process_voice
from src.tts import speak

def main():
    if run():
        text = process_voice()
        speak(text)

if __name__ == "__main__":
    main()