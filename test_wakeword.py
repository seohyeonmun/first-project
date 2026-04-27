import sounddevice as sd
import numpy as np
from openwakeword.model import Model
import pyttsx3

SAMPLE_RATE = 16000

print("모델 로딩 중...")
oww = Model(
    wakeword_models=["./wakeword_model/교통봇.onnx"],
    inference_framework="onnx",
    enable_speex_noise_suppression=False
)

# TTS 설정
engine = pyttsx3.init()
engine.setProperty('rate', 190)  # 속도 조절

print("✅ 모델 로딩 완료!")

THRESHOLD = 0.90
CONTINUOUS_COUNT = 4

def speak(text):
    engine.say(text)
    engine.runAndWait()

def test_wakeword():
    print("🎧 마이크 준비 중...")
    chunk_size = 1280
    detection_count = 0
    max_score = 0
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16') as stream:
        for _ in range(10):
            stream.read(chunk_size)
        
        print("✅ 준비 완료! '교통봇' 이라고 말해주세요!")
        print("(Ctrl+C 로 종료)\n")
        
        while True:
            chunk, _ = stream.read(chunk_size)
            chunk = np.array(chunk).flatten()
            
            prediction = oww.predict(chunk)
            score = list(prediction.values())[0]
            
            if score > THRESHOLD:
                detection_count += 1
                max_score = max(max_score, score)
                print(f"🔄 연속 감지: {detection_count}/{CONTINUOUS_COUNT} (score: {score:.4f})")
            else:
                detection_count = 0
                max_score = 0
            
            if detection_count >= CONTINUOUS_COUNT:
                print(f"✅ 호출어 감지! (최고 score: {max_score:.4f})")
                speak("네, 무엇을 도와드릴까요?")
                
                # 초기화 + 워밍업
                oww.reset()
                detection_count = 0
                max_score = 0
                
                for _ in range(20):
                    stream.read(chunk_size)

if __name__ == "__main__":
    test_wakeword()