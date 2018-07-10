import wave
import contextlib
fname = "output.wav"
with contextlib.closing(wave.open(fname, 'r')) as f:
    frames = f.getnframes()
    rate = f.getframerate()
    duration = frames / float(rate)
    print(duration)