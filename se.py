# -*- coding: utf-8 -*-
import pyaudio
import wave
import os
import random

# 効果音を鳴らす https://qiita.com/Nyanpy/items/cb4ea8dc4dc01fe56918#2pyaudio
def play_main(filename):
    CHUNK = 1024
    p = pyaudio.PyAudio()

    wf = wave.open(filename, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)
    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)
    stream.stop_stream()
    stream.close()
    return

def play(check):
    if check == True:
        se_dir = os.path.dirname(os.path.abspath(__file__)) + '/se_ok/'
    else:
        se_dir  = os.path.dirname(os.path.abspath(__file__)) + '/se_bad/'

    temp = os.listdir(se_dir)
    se_name = random.choice(temp)
    play_main(se_dir + se_name)
