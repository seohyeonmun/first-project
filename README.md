# voice-assistant-mvp

KWS(웨이크워드)로 호출해서 음성 명령을 텍스트로 변환하고, 로컬 OpenClaw 에이전트로 답변 생성 후 TTS로 재생하는 최소 MVP.

## Pipeline

1. Wake word 감지 (openWakeWord, 선택적으로 Silero VAD 게이팅)
2. 확인 응답 "네?" 출력 후 2초 내 음성 시작 감지
3. 무음 기반 녹음 (기본: 무음 3초 감지 시 종료)
4. STT (faster-whisper)
5. `openclaw agent --local`로 답변 생성
6. TTS 재생 (GPT-SoVITS only: `gpt_sovits_api` 권장, `gpt_sovits` 로컬 옵션)

## Quick Start

```bash
cd projects/voice-assistant-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Required env

- 별도 OpenAI API 키 불필요 (로컬 OpenClaw 인증/모델 설정 사용)

## MiniMax TTS 데이터셋 생성 스크립트

MiniMax에서 이미 학습된 `voice_id`가 있다면 문장 파일을 일괄 합성해서 과제용 데이터셋(`wavs/ + metadata.csv`)을 만들 수 있음.

```bash
cd projects/voice-assistant-mvp

# 1) 문장 자동 생성 (예: 400문장)
python3 scripts/generate_sentences_kr.py \
  --count 400 \
  --out artifacts/tts-dataset/sentences.txt

# 2) MiniMax TTS로 WAV 일괄 생성
export MINIMAX_API_KEY="<YOUR_KEY>"
# export MINIMAX_GROUP_ID="<YOUR_GROUP_ID>"   # 필요할 때만

python3 scripts/minimax_tts_dataset.py \
  --sentences artifacts/tts-dataset/sentences.txt \
  --out-dir artifacts/tts-dataset \
  --voice-id "<YOUR_VOICE_ID>" \
  --audio-format wav \
  --output-format hex
```

생성 결과:

- `artifacts/tts-dataset/wavs/*.wav`
- `artifacts/tts-dataset/metadata.csv` (`wavs/xxx.wav|문장`)

## TTS backend (GPT-SoVITS only)

이 프로젝트의 TTS는 GPT-SoVITS만 사용한다.

```bash
# 권장: 상시 API 모드 (모델 warm 유지)
TTS_BACKEND=gpt_sovits_api
GPT_SOVITS_USE_API=1
GPT_SOVITS_API_URL=http://127.0.0.1:9880
GPT_SOVITS_API_TIMEOUT=90

# 로컬 추론 모드(필요 시)
# TTS_BACKEND=gpt_sovits
# GPT_SOVITS_DIR=/Volumes/t7/openclaw-storage/projects/GPT-SoVITS
# GPT_SOVITS_PYTHON=/Volumes/t7/openclaw-storage/projects/GPT-SoVITS/.venv/bin/python

# 공통 파라미터
GPT_SOVITS_REF_AUDIO=/absolute/path/to/reference.wav
GPT_SOVITS_REF_TEXT=핵심은 다음 점검 시점은 1시간 내에 확인 가능이에요.
GPT_SOVITS_PROMPT_LANGUAGE=all_ko
GPT_SOVITS_TEXT_LANGUAGE=all_ko
GPT_SOVITS_TEXT_SPLIT_METHOD=cut0
GPT_SOVITS_SAMPLE_STEPS=4
GPT_SOVITS_TOP_K=20
GPT_SOVITS_TOP_P=0.6
GPT_SOVITS_TEMPERATURE=0.6
```

서버 실행 예시:

```bash
cd /Volumes/t7/openclaw-storage/projects/GPT-SoVITS
./.venv/bin/python api_v2.py -a 127.0.0.1 -p 9880 -c GPT_SoVITS/configs/tts_infer.yaml
```

동작:

- `gpt_sovits_api`: 상시 구동 중인 GPT-SoVITS `api_v2`로 요청(모델 warm) → WAV 저장 → `afplay`
- `gpt_sovits`: 로컬 GPT-SoVITS 스크립트 추론 → WAV 저장 → `afplay`

오류 시 자동으로 `say` fallback 한다(서비스 중단 방지용).

## Latency profiling

`VOICE_TIMING_LOG=1`이면 런타임에 아래 단계별 지연이 로그로 출력된다.

- `record.capture`
- `stt.transcribe`
- `llm.ask`
- `tts.speak` + TTS 내부 세부(`tts.melo_synthesize`, `tts.openvoice2_clone`, `tts.rvc_convert` 등)
- `end_to_end`

## Notes

- 기본값은 openWakeWord 기본 모델(`OWW_DEFAULT_MODEL=alexa`)로 동작.
- `USE_SILERO_VAD=1`이면 Silero VAD가 말소리 구간만 열어줘서 KWS 오탐/CPU 사용량을 줄일 수 있음.
- 커스텀 호출어 `클로야`를 쓰려면 커스텀 모델 파일(`OWW_MODEL_PATH`)을 나중에 붙이면 됨.
- 축약 명령 지원: `강남 몇분?`, `대림 몇분?` 같은 짧은 문장을 신림역 2호선 기준 표준 질의로 자동 확장.
- 데모용 로그/오디오는 `artifacts/`에 저장됨.
