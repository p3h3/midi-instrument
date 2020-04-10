import pygame
import pygame.midi
import pyaudio
import numpy as np
import threading
import math
from time import sleep
from pygame.locals import *

try:  # Ensure set available for output example
    set
except NameError:
    from sets import Set as set

note_names = ["C",
         "C#",
         "D",
         "D#",
         "E",
         "F",
         "F#",
         "G",
         "G#",
         "A",
         "A#",
         "H"]

fs = 44100      # sampling rate, Hz, must be integer
a4 = 440        #A4 tuning frequency
buffer_size = 16000
last_phase = {}
buffer = (0*np.arange(buffer_size)).astype(np.float32)

keys = {}
pitch_wheel = 64


def compute_buffer():
    global last_phase
    global buffer
    temp_buffer = (0*np.arange(buffer_size)).astype(np.float32)
    for i in range(1, len(keys)):
        if(keys[i]['pressed']):
            velocity = keys[i]['velocity'] / 127
            frequency = keys[i]['frequency'] * (pitch_wheel / 64)
            offset = (np.arcsin(last_phase[i]) / (2*np.pi)) * (1/frequency) * fs
            samples = ((np.sin(2*np.pi*(np.arange(buffer_size)+offset)*frequency/fs)).astype(np.float32)) * velocity
            last_phase[i] = samples[len(samples)-1]/velocity
            temp_buffer = (np.add(samples, buffer) / 2)
    buffer = temp_buffer

def generate_sound():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=fs,
                output=True)
    
    global last_phase
    for i in range(0,144):
        last_phase[i] = 0
    
    while True:
        stream.write(buffer)
        compute_thread = threading.Thread(target=compute_buffer)
        compute_thread.start()

def init_keys():
    global keys
    for i in range(0,144):
        keys[i] = {}
        keys[i]['pressed'] = False
        keys[i]['velocity'] = 0
        key = i % 12
        octave = math.floor(i / 12)
        frequency = a4*(2**(3/12)) *(2**((key+((octave-4)*12))/12))
        keys[i]['name'] = note_names[key] + "^" + str(octave)
        keys[i]['frequency'] = frequency

def print_device_info():
    pygame.midi.init()
    for i in range( pygame.midi.get_count() ):
        r = pygame.midi.get_device_info(i)
        (interf, name, input, output, opened) = r

        in_out = ""
        if input:
            in_out = "(input)"
        if output:
            in_out = "(output)"

        print(str(i) + ": " + str(name) + " " + str(in_out))
    pygame.midi.quit()

def input_main(device_id = None):
    pygame.init()
    pygame.fastevent.init()
    event_get = pygame.fastevent.get
    event_post = pygame.fastevent.post
    pygame.midi.init()


    if device_id is None:
        input_id = pygame.midi.get_default_input_id()
    else:
        input_id = device_id

    print ("using input_id :%s:" % input_id)
    i = pygame.midi.Input( input_id )

    global pressed_keys
    global pitch_wheel

    going = True
    while going:
        events = event_get()
        for e in events:
            if e.type in [QUIT]:
                going = False
            if e.type in [KEYDOWN]:
                going = False
            if e.type in [pygame.midi.MIDIIN]:
                print (e)

        if i.poll():
            midi_events = i.read(10)
            # convert them into pygame events.
            midi_evs = pygame.midi.midis2events(midi_events, i.device_id)

            for m_e in midi_evs:
                if(m_e.status == 159):
                    if(m_e.data2 > 0):
                        keys[m_e.data1]['pressed'] = True
                        keys[m_e.data1]['velocity'] = m_e.data2
                    else:
                        keys[m_e.data1]['pressed'] = False
                if(m_e.status == 143):
                    keys[m_e.data1]['pressed'] = False
                    keys[m_e.data1]['velocity'] = 0
                if(m_e.status == 191):
                    print("automation input")
                if(m_e.status == 239):
                    pitch_wheel = m_e.data2

    del i
    stream.stop_stream()
    stream.close()
    p.terminate()
    pygame.midi.quit()

                
if __name__ == '__main__':

    print_device_info()
    
    try:
        device_id = int( sys.argv[-1] )
    except:
        device_id = None

    init_keys()
    audio_thread = threading.Thread(target=generate_sound)
    audio_thread.start()
    
    input_main(1)
