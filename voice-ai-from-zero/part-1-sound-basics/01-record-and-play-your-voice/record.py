# Record your voice for 5 seconds, play it back, and save it as my_voice.wav
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000      # 16,000 numbers per second: the rate speech AI models expect
SECONDS = 5

print("🎙️  Recording for 5 seconds... say something!")
audio = sd.rec(int(SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
sd.wait()                # wait until recording is finished
print("✅ Done. Playing it back...")

sd.play(audio, SAMPLE_RATE)
sd.wait()

sf.write("my_voice.wav", audio, SAMPLE_RATE)
print(f"💾 Saved my_voice.wav. It's {len(audio):,} numbers; the loudest one is {abs(audio).max():.2f} (1.0 = max).")
print("First 8 numbers of your voice:", audio[:8, 0].round(4))
