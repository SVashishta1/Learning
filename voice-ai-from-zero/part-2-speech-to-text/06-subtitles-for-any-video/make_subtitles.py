# Make a subtitle file (.srt) for any video or audio. Video players like VLC load it automatically.
# Usage: python make_subtitles.py my_video.mp4
import sys
from pathlib import Path

from faster_whisper import WhisperModel


def srt_time(seconds):
    """3.5 -> '00:00:03,500' (the format .srt files use)"""
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(segments):
    blocks = []
    for number, seg in enumerate(segments, start=1):
        blocks.append(f"{number}\n{srt_time(seg.start)} --> {srt_time(seg.end)}\n{seg.text.strip()}\n")
    return "\n".join(blocks)


if __name__ == "__main__":
    video = Path(sys.argv[1])
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(video), vad_filter=True)     # works on video files too (it reads the audio)
    print(f"Language: {info.language} | length: {info.duration:.0f} s. Transcribing...")
    segments = list(segments)                                            # the transcription happens here
    out = video.with_suffix(".srt")
    out.write_text(to_srt(segments), encoding="utf-8")
    print(f"✅ Wrote {len(segments)} subtitles to {out.name}. Open the video in VLC: subtitles appear automatically.")
