from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_path(value: str, base: Path) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


def _speak_say(text: str, voice: str) -> None:
    os_name = platform.system()

    if os_name == "Windows":
        try:
            import pyttsx3

            engine = pyttsx3.init()
            if voice:
                v_lower = voice.lower()
                for v in engine.getProperty("voices") or []:
                    name = str(getattr(v, "name", "")).lower()
                    if v_lower in name:
                        engine.setProperty("voice", v.id)
                        break
            engine.say(text)
            engine.runAndWait()
        except Exception:
            # pyttsx3 미설치/초기화 실패 시 최소 동작 보장
            print(text)
        return

    if os_name == "Darwin":
        subprocess.run(["say", "-v", voice, text], check=False)
        return

    # Linux/기타
    subprocess.run(["espeak", text], check=False)


def _play_wav(path: Path) -> None:
    os_name = platform.system()

    if os_name == "Windows":
        import winsound

        winsound.PlaySound(str(path), winsound.SND_FILENAME)
        return

    if os_name == "Darwin":
        _run(["afplay", str(path)])
        return

    _run(["aplay", str(path)])


def _timing_enabled() -> bool:
    return os.getenv("VOICE_TIMING_LOG", "1") == "1"


def _normalize_for_tts(text: str) -> str:
    s = (text or "").strip()
    if not s:
        return ""

    # Strip markdown/control noise that sounds unnatural when spoken.
    s = s.replace("```", " ")
    s = re.sub(r"[*_`#>~]+", "", s)

    # Remove common progress-bar/log fragments (e.g., '13%|██▊ | 199/1500').
    s = re.sub(r"\b\d+%\|[^\n]{0,40}\|\s*\d+/\d+", "", s)

    # Drop debug-style lines sometimes copied from inference logs.
    s = re.sub(r"실제 입력된 목표 텍스트\([^\)]*\):", "", s)
    s = re.sub(r"프론트엔드 처리 후 텍스트\([^\)]*\):", "", s)

    # Collapse repeated whitespace.
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _log_timing(label: str, start: float) -> None:
    if _timing_enabled():
        print(f"[LATENCY] {label}: {(time.perf_counter() - start) * 1000:.0f}ms")


def _log_tts_config(label: str, **kwargs: str) -> None:
    if not _timing_enabled():
        return
    fields = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    print(f"[TTS-CONFIG] {label} {fields}".strip())


def _run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=merged_env, check=True)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _runtime_wavs(prefix: str) -> tuple[Path, Path]:
    workspace = _workspace_root()
    project_dir = workspace / "projects" / "voice-assistant-mvp"
    runtime_dir = project_dir / "artifacts" / "runtime_tts"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time() * 1000)
    return runtime_dir / f"{prefix}_{ts}.wav", runtime_dir / f"jarvis_{ts}.wav"


def _speak_via_gpt_sovits(text: str) -> None:
    workspace = _workspace_root()
    project_dir = workspace / "projects" / "voice-assistant-mvp"
    gsv_wav, _ = _runtime_wavs("gpt_sovits")

    gsv_script = project_dir / "scripts" / "gpt_sovits_tts.py"

    gsv_dir_raw = os.getenv("GPT_SOVITS_DIR", "").strip()
    if not gsv_dir_raw:
        raise EnvironmentError(
            "GPT_SOVITS_DIR is required. Set it in your .env (see .env.example)."
        )

    gsv_dir = _resolve_path(gsv_dir_raw, project_dir)
    gsv_python = os.getenv("GPT_SOVITS_PYTHON", str(gsv_dir / ".venv" / "bin" / "python"))

    gsv_gpt_model = os.getenv("GPT_SOVITS_GPT_MODEL", "GPT_SoVITS/pretrained_models/s1v3.ckpt")
    gsv_sovits_model = os.getenv("GPT_SOVITS_SOVITS_MODEL", "GPT_SoVITS/pretrained_models/s2Gv3.pth")
    gsv_ref_audio = os.getenv("GPT_SOVITS_REF_AUDIO", "")
    gsv_ref_text = os.getenv("GPT_SOVITS_REF_TEXT", "")
    gsv_prompt_lang = os.getenv("GPT_SOVITS_PROMPT_LANGUAGE", "all_ko")
    gsv_text_lang = os.getenv("GPT_SOVITS_TEXT_LANGUAGE", "all_ko")
    gsv_how_to_cut = os.getenv("GPT_SOVITS_HOW_TO_CUT", "不切")
    gsv_top_k = os.getenv("GPT_SOVITS_TOP_K", "20")
    gsv_top_p = os.getenv("GPT_SOVITS_TOP_P", "0.6")
    gsv_temperature = os.getenv("GPT_SOVITS_TEMPERATURE", "0.6")
    gsv_speed = os.getenv("GPT_SOVITS_SPEED", "1.0")
    gsv_pause_second = os.getenv("GPT_SOVITS_PAUSE_SECOND", "0.3")
    gsv_sample_steps = os.getenv("GPT_SOVITS_SAMPLE_STEPS", "8")

    if not gsv_ref_audio:
        raise ValueError("GPT_SOVITS_REF_AUDIO is required")

    _log_tts_config(
        "gpt_sovits.local",
        sample_steps=gsv_sample_steps,
        text_language=gsv_text_lang,
        prompt_language=gsv_prompt_lang,
        how_to_cut=gsv_how_to_cut,
        top_k=gsv_top_k,
        top_p=gsv_top_p,
        temperature=gsv_temperature,
    )

    cmd = [
        gsv_python,
        str(gsv_script),
        "--text",
        text,
        "--out",
        str(gsv_wav),
        "--gpt-sovits-dir",
        str(gsv_dir),
        "--gpt-model",
        gsv_gpt_model,
        "--sovits-model",
        gsv_sovits_model,
        "--ref-audio",
        gsv_ref_audio,
        "--ref-text",
        gsv_ref_text,
        "--prompt-language",
        gsv_prompt_lang,
        "--text-language",
        gsv_text_lang,
        "--how-to-cut",
        gsv_how_to_cut,
        "--top-k",
        gsv_top_k,
        "--top-p",
        gsv_top_p,
        "--temperature",
        gsv_temperature,
        "--speed",
        gsv_speed,
        "--pause-second",
        gsv_pause_second,
        "--sample-steps",
        gsv_sample_steps,
    ]

    t0 = time.perf_counter()
    _run(cmd)
    _log_timing("tts.gpt_sovits_synthesize", t0)
    _play_wav(gsv_wav)


def _speak_via_gpt_sovits_api(text: str) -> None:
    gsv_wav, _ = _runtime_wavs("gpt_sovits_api")

    api_url = os.getenv("GPT_SOVITS_API_URL", "https://api.portfolio-corab.shop").rstrip("/")
    timeout_sec = float(os.getenv("GPT_SOVITS_API_TIMEOUT", "90"))
    speaker_id = os.getenv("GPT_SOVITS_SPEAKER_ID", "").strip()

    params = {
        "text": text,
        "text_lang": os.getenv("GPT_SOVITS_TEXT_LANGUAGE", "all_ko"),
        "prompt_lang": os.getenv("GPT_SOVITS_PROMPT_LANGUAGE", "all_ko"),
        "prompt_text": os.getenv("GPT_SOVITS_REF_TEXT", ""),
        "text_split_method": os.getenv("GPT_SOVITS_TEXT_SPLIT_METHOD", "cut0"),
        "batch_size": os.getenv("GPT_SOVITS_BATCH_SIZE", "1"),
        "batch_threshold": os.getenv("GPT_SOVITS_BATCH_THRESHOLD", "0.75"),
        "split_bucket": str(_env_bool("GPT_SOVITS_SPLIT_BUCKET", True)).lower(),
        "speed_factor": os.getenv("GPT_SOVITS_SPEED", "1.0"),
        "fragment_interval": os.getenv("GPT_SOVITS_FRAGMENT_INTERVAL", "0.3"),
        "seed": os.getenv("GPT_SOVITS_SEED", "-1"),
        "media_type": "wav",
        "streaming_mode": os.getenv("GPT_SOVITS_STREAMING_MODE", "False"),
        "parallel_infer": str(_env_bool("GPT_SOVITS_PARALLEL_INFER", True)).lower(),
        "repetition_penalty": os.getenv("GPT_SOVITS_REPETITION_PENALTY", "1.35"),
        "sample_steps": os.getenv("GPT_SOVITS_SAMPLE_STEPS", "8"),
        "super_sampling": str(_env_bool("GPT_SOVITS_SUPER_SAMPLING", False)).lower(),
        "top_k": os.getenv("GPT_SOVITS_TOP_K", "20"),
        "top_p": os.getenv("GPT_SOVITS_TOP_P", "0.6"),
        "temperature": os.getenv("GPT_SOVITS_TEMPERATURE", "0.6"),
    }

    if not speaker_id:
        raise ValueError("API mode requires GPT_SOVITS_SPEAKER_ID. Query /speakers on the server.")
    params["speaker_id"] = speaker_id

    _log_tts_config(
        "gpt_sovits.api",
        api_url=api_url,
        speaker_id=(speaker_id or "<legacy-ref-audio>"),
        sample_steps=str(params["sample_steps"]),
        text_lang=str(params["text_lang"]),
        prompt_lang=str(params["prompt_lang"]),
        split_method=str(params["text_split_method"]),
        batch_size=str(params["batch_size"]),
        parallel_infer=str(params["parallel_infer"]),
        streaming_mode=str(params["streaming_mode"]),
    )

    url = f"{api_url}/tts?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": os.getenv("GPT_SOVITS_API_USER_AGENT", "openclaw-voice-assistant/1.0"),
            "Accept": "audio/wav,*/*;q=0.8",
        },
    )

    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = resp.read()
        content_type = (resp.headers.get("Content-Type") or "").lower()

    if not payload:
        raise RuntimeError("GPT-SoVITS API returned empty audio")
    if "application/json" in content_type:
        detail = payload.decode("utf-8", errors="replace")
        try:
            obj = json.loads(detail)
            detail = obj.get("message") or obj.get("error") or detail
        except Exception:
            pass
        raise RuntimeError(f"GPT-SoVITS API error: {detail}")

    gsv_wav.write_bytes(payload)
    _log_timing("tts.gpt_sovits_api", t0)
    _play_wav(gsv_wav)


def speak(text: str, voice: str = "Yuna") -> None:
    safe_text = _normalize_for_tts(text) or "응답이 비어 있어요."
    backend = os.getenv("TTS_BACKEND", "gpt_sovits_api").strip().lower()
    total_t0 = time.perf_counter()

    # 짧은 문장도 포함해 항상 GPT-SoVITS 경로를 우선 시도한다.

    try:
        use_api = backend == "gpt_sovits_api" or _env_bool("GPT_SOVITS_USE_API", True)
        _log_tts_config("gpt_sovits.route", backend=backend, resolved_mode=("api" if use_api else "local"))
        if use_api:
            _speak_via_gpt_sovits_api(safe_text)
        else:
            _speak_via_gpt_sovits(safe_text)
    except Exception as e:
        print(f"[TTS] gpt_sovits fallback to say: {e}")
        say_t0 = time.perf_counter()
        _speak_say(safe_text, voice)
        _log_timing("tts.say_fallback", say_t0)
    finally:
        _log_timing(f"tts.total[{backend}]", total_t0)
