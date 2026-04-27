# 교통봇 호출어 감지 모델

## 📌 개요
openWakeWord 기반으로 파인튜닝한 한국어 호출어 감지 모델입니다.
**"교통봇"** 이라고 말하면 자동으로 감지하여 음성으로 응답합니다.

---

## 📁 파일 구조
```
├── wakeword_model/
│   └── 교통봇.onnx       ← 파인튜닝된 호출어 감지 모델
├── test_wakeword.py       ← 테스트 코드
├── requirements.txt       ← 필요한 패키지 목록
└── README.md              ← 사용 설명서
```

---

## ⚙️ 설치 방법

### 1. Python 버전 확인
```bash
python --version  # 3.10 이상 필요
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. ffmpeg 설치 (Windows)
- https://www.gyan.dev/ffmpeg/builds/ 에서 다운로드
- `C:\ffmpeg\bin` 에 설치 후 환경변수 등록

---

## 🚀 사용 방법

### 실행
```bash
python test_wakeword.py
```

### 동작 순서
```
1. 프로그램 실행
2. "✅ 준비 완료!" 메시지 확인
3. "교통봇" 이라고 말하기
4. "네, 말씀하세요" 음성 응답 확인
```

---

## 🎤 호출어
| 호출어 | 감지 여부 |
|--------|---------|
| **교통봇** | ✅ 감지 |
| 교통안내 | ⚠️ 일부 감지 (오탐 가능) |
| 기타 단어 | ❌ 미감지 |

---

## 📦 주요 패키지
| 패키지 | 용도 |
|--------|------|
| openwakeword | 호출어 감지 모델 |
| sounddevice | 마이크 입력 |
| pyttsx3 | 음성 응답 (TTS) |
| numpy | 오디오 데이터 처리 |

---

## 🔧 설정 변경 (`test_wakeword.py`)
```python
THRESHOLD = 0.90       # 감지 임계값 (높을수록 정확, 낮을수록 민감)
CONTINUOUS_COUNT = 4   # 연속 감지 횟수 (높을수록 정확)
engine.setProperty('rate', 150)  # 음성 속도 (100~300)
```

---

## 🎙️ 마이크 문제 해결

### 마이크 목록 확인
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### 마이크 볼륨 테스트
```bash
python -c "
import sounddevice as sd
import numpy as np

with sd.InputStream(samplerate=16000, channels=1, dtype='int16') as stream:
    for i in range(10):
        chunk, _ = stream.read(1280)
        print(f'볼륨: {np.max(np.abs(chunk))}')
"
```
> 말할 때 볼륨이 1000 이상 나오면 정상입니다

### 문제별 해결 방법

#### ❌ 마이크가 아예 인식 안 될 때
1. Windows 설정 → 개인 정보 → 마이크 → **앱의 마이크 액세스 허용** 켜기
2. 장치 관리자에서 마이크 드라이버 재설치

#### ❌ 볼륨이 너무 낮을 때 (볼륨 10 이하)
1. 작업표시줄 🔊 우클릭 → **소리 설정**
2. 입력 → 마이크 선택 → **볼륨 100%** 로 올리기
3. `test_wakeword.py` 에서 device 번호 변경
```python
# 마이크 목록에서 > 표시된 번호로 변경
with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=1) as stream:
```

#### ❌ 여러 마이크가 있을 때
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```
출력 결과에서 `>` 표시된 번호가 기본 마이크입니다.
`test_wakeword.py` 에서 원하는 마이크 번호로 변경:
```python
with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', device=번호) as stream:
```

#### ❌ PortAudio 오류가 날 때
```bash
pip install sounddevice --upgrade
```

#### ❌ 인식은 되는데 score가 낮을 때
- 마이크에 가까이 대고 말해주세요
- 조용한 환경에서 테스트해주세요
- THRESHOLD 값을 낮춰보세요 (0.90 → 0.80)

---

## ⚠️ 주의사항
- 마이크가 연결되어 있어야 합니다
- 조용한 환경에서 사용하면 인식률이 높아집니다
- 처음 실행 시 모델 로딩에 약 6초 소요됩니다
- Windows 환경에서 테스트되었습니다

---

## 📞 문의
프로젝트 관련 문의는 팀원에게 연락해주세요.
