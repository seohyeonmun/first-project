# TTS 업로드 체크리스트 (GPT-SoVITS only)

## ✅ 올릴 파일(권장 최소 세트)

- `src/tts.py`
- `scripts/gpt_sovits_tts.py`
- `.env.example`
- `requirements.txt`
- `README.md`
- `docs/interface-spec.md`
- `docs/tts-github-upload-checklist.md`
- `.gitignore`

## ❌ 올리면 안 되는 파일

- `.env` (토큰/키)
- `artifacts/`, `processed/`, `logs/`, `output/`, `outputs/`
- 모델/가중치 파일 (`*.pth`, `*.ckpt`, `*.safetensors`, `*.onnx`, `*.gguf`, `*.bin`)
- 런타임 오디오 (`*.wav`, `*.mp3`, `*.flac`)

## 추천 업로드 절차

```bash
cd projects/voice-assistant-mvp

git status

git add src/tts.py scripts/gpt_sovits_tts.py .env.example requirements.txt README.md docs/interface-spec.md docs/tts-github-upload-checklist.md .gitignore

git status
# staged 목록이 위 파일과 동일한지 확인

git commit -m "feat(tts): gpt-sovits-only path and upload-safe gitignore"
```

## 주의

- 실수로 `.env`/키가 올라갔다면 즉시 키 재발급(rotate) 필요
- 모델 파일은 GitHub가 아니라 외부 스토리지/HF/드라이브 링크로 공유
