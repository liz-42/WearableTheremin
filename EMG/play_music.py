import numpy as np
import pyaudio
import pickle
import serial
import time
import math
import threading

# factors - 260 - 24
notes = {130: "C3",
         # 138: "C#3",
         146: "D3",
         # 156: "D#3",
         164: "E3",
         174: "F3",
         # 186: "F#3",
         196: "G3",
         # 208: "G#3",
         220: "A3",
         # 234: "A#3",
         246: "B3",
         262: "C4",
         # 278: "C#4",
         294: "D4",
         # 312: "D#4",
         330: "E4",
         350: "F4",
         # 370: "F#4",
         392: "G4",
         # 416: "G#4",
         440: "A4",
         # 466: "A#4",
         494: "B4",
         524: "C5",
         # 554: "C#5",
         588: "D5",
         # 622: "D#5",
         660: "E5",
         698: "F5",
         # 740: "F#5",
         784: "G5",
         # 830: "G#5",
         880: "A5",
         # 932: "A#5",
         988: "B5"}


port = serial.Serial("COM5", 9600)
port2 = serial.Serial("COM9", 115200)


# read in model and scaler
model = pickle.load(open("finalized_model.sav", 'rb'))
scaler = pickle.load(open("model_scaler.sav", 'rb'))

p = pyaudio.PyAudio()

volume = 1.0     # range [0.0, 1.0]
fs = 44100       # sampling rate, Hz, must be integer
duration = 1.0   # in seconds, may be float
f = 246        # sine frequency, Hz, may be float

# generate samples, note conversion to float32 array
samples = (np.sin(2*np.pi*np.arange(fs*duration)*f/fs)).astype(np.float32)

sound_val = samples

def round_even(x):
    return round(x/2.)*2

def read_frequency():
    global samples
    port2.flush()
    prev_freq = 0
    while True:
        t2 = time.time()
        elapsed_time2 = 0
        pitch_step = 1
        while elapsed_time2 < 0.01:
            pitch_step = int(port2.readline().decode().strip())
            elapsed_time2 = time.time() - t2
        factor = 2 ** (pitch_step/12)
        freq = 246 * factor
        freq = freq or min(notes.keys(), key=lambda key: abs(key - freq))
        # freq = round_even(freq)
        # print note out to console
        if freq != prev_freq:
            if freq in notes:
                print(notes[freq])
            else:
                closest = 130  #first key
                for key in notes:
                    if abs(key - freq) < abs(key - closest):
                        closest = key
                print(notes[closest])
                freq = closest
            prev_freq = freq
        samples = (np.sin(2 * np.pi * np.arange(fs * duration) * freq / fs)).astype(np.float32)


# define callback (2)
def callback(in_data, frame_count, time_info, status):
    data = sound_val
    return (data, pyaudio.paContinue)

# for paFloat32 sample values must be in range [-1.0, 1.0]
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True,
                frames_per_buffer=22050,
                stream_callback=callback)

# play. May repeat with different volume values (if done interactively)
stream.start_stream()

freq_thread = threading.Thread(target=read_frequency)
freq_thread.start()

port.flush()
while True:
    gesture = []
    t = time.time()
    elapsed_time = 0
    while elapsed_time < 0.5:
        sound_val = samples * volume
        gesture.append(int(port.readline().decode().strip()))
        elapsed_time = time.time() - t
    # get features from the gesture
    offset = np.median(gesture)
    recentered = [(x - offset) for x in gesture]

    fft = np.fft.rfft(recentered)
    sr = (len(recentered))
    freqs = np.fft.rfftfreq(len(fft), 1 / sr)
    index = np.searchsorted(freqs, sr / 2)
    sound_val = samples * volume

    lowpass = fft[:]
    lowpass[index:] = 0
    filtered = np.fft.irfft(lowpass)

    rectified = np.abs(filtered)

    iav = np.sum(rectified)
    mav = np.sum(rectified)/len(rectified)
    rms = math.sqrt(np.sum(rectified ** 2) / len(rectified))
    sound_val = samples * volume

    std = np.std(filtered)
    var = np.var(filtered)

    count = 0
    for k in range(1, len(filtered)):
        sound_val = samples * volume
        count = count + abs(filtered[k] - filtered[k - 1])
    wl = count

    all_features = np.array([iav, mav, rms, std, var, wl])
    #all_features = np.transpose(all_features)
    #all_features = scaler.transform([all_features])

    result = model.predict([all_features])

    if result == "rest":
        volume = 0.01
    else:
        volume = 1.0

    sound_val = samples * volume

stream.stop_stream()
stream.close()

p.terminate()