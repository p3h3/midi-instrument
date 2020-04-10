import pygame
import pygame.midi
from array import array
import numpy as np
import threading
import math
from pygame.locals import *

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

sample_rate = 44100  # sampling rate, Hz, must be integer
a4 = 440             # A4 tuning frequency
buffer_size = 512

going = True

keys = {}
pitch_wheel = 64

class Note(pygame.mixer.Sound): 

    def __init__(self, frequency, volume=.1): 
        self.frequency = frequency 
        pygame.mixer.Sound.__init__(self, self.build_samples()) 
        self.set_volume(volume) 

    def build_samples(self): 
        period = int(round(pygame.mixer.get_init()[0] / self.frequency)) 
        samples = array("h", [0] * period) 
        amplitude = 2 ** (abs(pygame.mixer.get_init()[1]) - 1) - 1 
        for time in range(period): 
            if time < period / 2: 
                samples[time] = amplitude 
            else: 
                samples[time] = -amplitude 
        return samples

def init_mixer():
    pygame.mixer.pre_init(sample_rate, -16, 1, buffer_size)
    pygame.init()
    screen = pygame.display.set_mode([1, 1], 0) 

def generate_sound():
    while going:
        for i in range(0, len(keys)):
            if(keys[i]['pressed']):
                keys[i]['note'].play(-1)
            else:
                keys[i]['note'].stop()

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
        keys[i]['note'] = Note(frequency)

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

    print ("Using input_id: %s" % input_id)
    i = pygame.midi.Input( input_id )

    global pressed_keys
    global pitch_wheel
    global going

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

    init_mixer();
        
    init_keys()

    audio_thread = threading.Thread(target=generate_sound)
    audio_thread.start()

    try:
        input_main(int(input("Which device do you want to use?")))
    except KeyboardInterrupt:
        pygame.quit()
        print("Exiting..")
    except:
        pygame.quit()
        print("There was an issue with the input device.")
