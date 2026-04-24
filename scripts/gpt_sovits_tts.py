from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _resolve_path(base: Path, value: str) -> Path:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


def _resolve_language_key(dict_language: dict[str, str], requested: str) -> str:
    req = (requested or "").strip()
    if req in dict_language:
        return req
    for k, v in dict_language.items():
        if v == req:
            return k

    aliases = {
        "ko": {"ko", "all_ko", "korean", "한국어", "한글", "韩文"},
        "ja": {"ja", "all_ja", "japanese", "日文", "일본어"},
        "en": {"en", "english", "英文", "영어"},
        "zh": {"zh", "all_zh", "chinese", "中文", "중국어"},
    }
    low = req.lower()
    if low in aliases["ko"]:
        for k, v in dict_language.items():
            if v == "all_ko":
                return k
    if low in aliases["ja"]:
        for k, v in dict_language.items():
            if v == "all_ja":
                return k
    if low in aliases["en"]:
        for k, v in dict_language.items():
            if v == "en":
                return k
    if low in aliases["zh"]:
        for k, v in dict_language.items():
            if v == "all_zh":
                return k

    raise ValueError(f"Unsupported language '{requested}'. available={list(dict_language.keys())}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TTS with local GPT-SoVITS and save wav")
    parser.add_argument("--text", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--gpt-sovits-dir", required=True)
    parser.add_argument("--gpt-model", required=True)
    parser.add_argument("--sovits-model", required=True)
    parser.add_argument("--ref-audio", required=True)
    parser.add_argument("--ref-text", required=True)
    parser.add_argument("--prompt-language", default="all_ko")
    parser.add_argument("--text-language", default="all_ko")
    parser.add_argument("--how-to-cut", default="不切")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--top-p", type=float, default=0.6)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--pause-second", type=float, default=0.3)
    parser.add_argument("--sample-steps", type=int, default=8)
    args = parser.parse_args()

    root = _resolve_path(Path.cwd(), args.gpt_sovits_dir)
    if not root.exists():
        raise FileNotFoundError(f"GPT-SoVITS dir not found: {root}")

    os.chdir(root)
    sys.path.insert(0, str(root))

    # first-run lang detector download path
    (root / "GPT_SoVITS" / "pretrained_models" / "fast_langdetect").mkdir(parents=True, exist_ok=True)

    import scipy.io.wavfile as wavfile
    import GPT_SoVITS.inference_webui as iw

    gpt_model = _resolve_path(root, args.gpt_model)
    sovits_model = _resolve_path(root, args.sovits_model)
    ref_audio = _resolve_path(root, args.ref_audio)
    out_path = _resolve_path(root, args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Must consume generator fully to avoid local var init bug in upstream code.
    for _ in iw.change_sovits_weights(str(sovits_model), prompt_language="韩文", text_language="韩文"):
        pass
    iw.change_gpt_weights(str(gpt_model))

    prompt_lang_key = _resolve_language_key(iw.dict_language, args.prompt_language)
    text_lang_key = _resolve_language_key(iw.dict_language, args.text_language)

    opt_sr, audio = next(
        iw.get_tts_wav(
            ref_wav_path=str(ref_audio),
            prompt_text=args.ref_text,
            prompt_language=prompt_lang_key,
            text=args.text,
            text_language=text_lang_key,
            how_to_cut=args.how_to_cut,
            top_k=args.top_k,
            top_p=args.top_p,
            temperature=args.temperature,
            ref_free=False,
            speed=args.speed,
            if_freeze=False,
            inp_refs=None,
            sample_steps=args.sample_steps,
            if_sr=False,
            pause_second=args.pause_second,
        )
    )
    wavfile.write(str(out_path), opt_sr, audio)
    print(str(out_path))


if __name__ == "__main__":
    main()
