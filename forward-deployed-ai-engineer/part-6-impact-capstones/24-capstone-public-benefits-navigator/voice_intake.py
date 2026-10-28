"""voice_intake.py: say your story out loud instead of typing it. Speech-to-text runs 100% on this computer.

    pip install faster-whisper "av<19"                      (once; the same as voice-ai-from-zero lesson 05)
    python voice_intake.py my_story.wav                      -> prints the text
    python voice_intake.py my_story.wav --send http://localhost:8000   -> also starts a navigator session

Record a WAV with voice-ai-from-zero/part-1-sound-basics/01-record-and-play-your-voice/record.py, or any recorder.
Whisper detects the language by itself (English, Spanish, Polish, ...). The audio never leaves your machine;
the text then goes through the same PII redaction as typed text.
"""
import argparse
import sys
from pathlib import Path


def transcribe(path: str, model_size: str = "small") -> tuple[str, str]:
    from faster_whisper import WhisperModel                    # imported here: only voice users need it
    model = WhisperModel(model_size, device="cpu", compute_type="int8")   # int8 = small and fast on a laptop CPU
    segments, info = model.transcribe(path)
    return " ".join(s.text.strip() for s in segments), info.language


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("audio")
    ap.add_argument("--model", default="small", help="tiny, base, small, medium (bigger = better and slower)")
    ap.add_argument("--send", help="navigator URL, e.g. http://localhost:8000")
    args = ap.parse_args(argv)
    if not Path(args.audio).exists():
        sys.exit(f"Can't find {args.audio}. Record a WAV first.")
    text, language = transcribe(args.audio, args.model)
    print(f"[{language}] {text}")
    if args.send:
        import httpx
        r = httpx.post(f"{args.send.rstrip('/')}/api/sessions", json={"story": text}, timeout=30)
        r.raise_for_status()
        print(f"Session started: open {args.send.rstrip('/')}/?session={r.json()['id']}")
    return text


if __name__ == "__main__":
    main()
