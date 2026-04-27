import sounddevice as sd
import numpy as np
from openwakeword.model import Model
import pyttsx3

SAMPLE_RATE = 16000
THRESHOLD = 0.90
CONTINUOUS_COUNT = 4

print("모델 로딩 중...")
oww = Model(
    wakeword_models=["./wakeword_model/교통봇.onnx"],
    inference_framework="onnx",
    enable_speex_noise_suppression=False
)

engine = pyttsx3.init()
engine.setProperty('rate', 190)
print("✅ 준비 완료!")

def speak(text):
    engine.say(text)
    engine.runAndWait()

def run():
    chunk_size = 1280
    detection_count = 0
    max_score = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
        for _ in range(10):
            stream.read(chunk_size)

        print("🎧 '교통봇' 이라고 말해주세요!")

        while True:
            chunk, _ = stream.read(chunk_size)
            chunk = np.array(chunk).flatten()

            prediction = oww.predict(chunk)
            score = list(prediction.values())[0]

            if score > THRESHOLD:
                detection_count += 1
                max_score = max(max_score, score)
            else:
                detection_count = 0
                max_score = 0

            if detection_count >= CONTINUOUS_COUNT:
                print("✅ 호출어 감지!")
                speak("네, 말씀하세요")

                # 초기화 + 워밍업
                oww.reset()
                detection_count = 0
                max_score = 0

                for _ in range(20):
                    stream.read(chunk_size)

                print("🎧 '교통봇' 이라고 말해주세요!")

if __name__ == "__main__":
    run()