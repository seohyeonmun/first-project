# Voice Pipeline Interface Spec (Team Contract)

Last updated: 2026-04-24  
Owner: Team Voice Assistant MVP

이 문서는 역할 분담 개발( KWS / STT+Bus API / TTS ) 시, 파이프라인이 끊기지 않도록 **모듈 간 I/O 규약**을 고정하기 위한 계약서입니다.

---

## 0) Goals

- 각자 브랜치에서 독립 개발 가능
- 통합 시 연결 오류 최소화
- 에러 포맷/타임아웃/재시도 기준 통일

---

## 1) Common Rules

### 1.1 Transport

- 내부 호출은 함수 호출 또는 HTTP 둘 다 허용
- 데이터 구조는 아래 JSON 스키마를 반드시 준수

### 1.2 Naming / Encoding

- 문자열: UTF-8
- 시간: ISO 8601 (`YYYY-MM-DDTHH:mm:ss.sssZ`)
- 필드명: `snake_case`

### 1.3 Trace

모든 단계는 `request_id`를 전달/유지한다.

- 예: `va_20260424_151500_ab12`

### 1.4 Common Error Format

```json
{
  "ok": false,
  "error": {
    "code": "STT_TIMEOUT",
    "message": "stt request timed out after 20s",
    "retryable": true
  },
  "request_id": "va_20260424_151500_ab12"
}
```

---

## 2) KWS → Orchestrator

### Event: `wake_detected`

```json
{
  "ok": true,
  "event": "wake_detected",
  "request_id": "va_20260424_151500_ab12",
  "wakeword": "헤이알렉스",
  "confidence": 0.92,
  "timestamp": "2026-04-24T06:15:00.123Z",
  "audio_device": "MacBook Air 마이크"
}
```

필수 필드:

- `event`, `request_id`, `wakeword`, `confidence`, `timestamp`

---

## 3) Orchestrator → STT

### Request

```json
{
  "request_id": "va_20260424_151500_ab12",
  "audio_path": "artifacts/cmd_1777000176.wav",
  "language": "ko",
  "max_audio_sec": 120
}
```

### Response

```json
{
  "ok": true,
  "request_id": "va_20260424_151500_ab12",
  "text": "신림역 2호선 강남 방향 다음 열차 언제 와?",
  "confidence": 0.89,
  "duration_sec": 3.7,
  "stt_model": "large-v3"
}
```

타임아웃 권장: 20초

---

## 4) Orchestrator → Bus API Module

### Request

```json
{
  "request_id": "va_20260424_151500_ab12",
  "query": "신림역 2호선 강남 방향 다음 2대",
  "user_context": {
    "timezone": "Asia/Seoul",
    "lang": "ko"
  }
}
```

### Response

```json
{
  "ok": true,
  "request_id": "va_20260424_151500_ab12",
  "answer_text": "강남 방향 다음 열차는 2분, 그다음은 6분 후 도착 예정입니다.",
  "source": "naver_map",
  "fetched_at": "2026-04-24T06:15:04.602Z"
}
```

타임아웃 권장: 8초

---

## 5) Orchestrator → LLM (optional)

Bus API 결과를 자연어로 다듬는 경우만 사용.

### Request

```json
{
  "request_id": "va_20260424_151500_ab12",
  "input_text": "강남 방향 다음 열차는 2분, 그다음은 6분 후 도착 예정입니다.",
  "style": "brief_korean_voice"
}
```

### Response

```json
{
  "ok": true,
  "request_id": "va_20260424_151500_ab12",
  "reply_text": "강남 방향은 2분, 다음 열차는 6분 뒤예요."
}
```

---

## 6) Orchestrator → TTS

### Request

```json
{
  "request_id": "va_20260424_151500_ab12",
  "text": "강남 방향은 2분, 다음 열차는 6분 뒤예요.",
  "voice": "Yuna",
  "backend": "gpt_sovits_api",
  "sample_steps": 4,
  "speed": 1.0
}
```

### Response

```json
{
  "ok": true,
  "request_id": "va_20260424_151500_ab12",
  "audio_path": "artifacts/runtime_tts/gpt_sovits_api_1777008021.wav",
  "latency_ms": 1420,
  "backend": "gpt_sovits_api"
}
```

타임아웃 권장: 15초

---

## 7) Playback Contract

### Request

```json
{
  "request_id": "va_20260424_151500_ab12",
  "audio_path": "artifacts/runtime_tts/gpt_sovits_api_1777008021.wav"
}
```

### Response

```json
{
  "ok": true,
  "request_id": "va_20260424_151500_ab12",
  "played": true
}
```

---

## 8) Minimum Integration Test Cases

1. `wake_detected` 수신 후 STT까지 성공
2. STT 결과를 Bus API에 전달 후 텍스트 응답 생성
3. 응답 텍스트를 TTS로 변환 후 재생 성공
4. STT timeout 시 공통 에러 포맷 반환
5. TTS backend 실패 시 fallback 동작(`say`) 확인

---

## 9) Branch / PR Workflow (권장)

- `feature/kws-*`
- `feature/stt-bus-*`
- `feature/tts-*`
- `integration/pipeline`에서 우선 통합 후 `main` 머지

PR 체크리스트:

- [ ] 이 스펙 필드명/타입 준수
- [ ] `request_id` 단계 간 유지
- [ ] timeout/retry 정책 반영
- [ ] 로컬 절대경로/비밀키 커밋 없음

---

## 10) Change Policy

스펙 변경은 반드시 PR로 진행:

- `Spec-Version` 헤더 증가 (`v1 -> v1.1`)
- 변경 이유 + 영향 모듈 명시
- 최소 2명 승인 후 적용
