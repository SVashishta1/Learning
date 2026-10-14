# 03 · Voice recorder in the browser

**What it does:** a web page that records your voice with a live volume meter and plays the recordings back. No Python and no install, just one HTML file.

## Run it
Browsers only allow the microphone on secure pages or `localhost`, so serve the folder:
```bash
cd part-1-sound-basics/03-voice-recorder-in-the-browser
python -m http.server 8000
```
Open http://localhost:8000/recorder.html, click **Start recording**, allow the microphone, talk, and click **Stop**.

## The idea in one sentence
Browsers have a built-in microphone (`getUserMedia`), recorder (`MediaRecorder`) and sound analyser (`AnalyserNode`), and in project 07 you'll run Whisper right here too.

## Try this
1. Make the meter turn red when you're too loud (loudness above 0.25).
2. Add a timer that shows how many seconds you've been recording.
