import pygame
import numpy
import math
#pygame.init()

bits = 16
sample_rate = 44100


def sine_t(amp, t, freq):
    return int(round( amp * math.sin( 2 * math.pi * freq * t )))


class Tone:
        
    def __init__(self, freq, vol, speaker=None, fade_ms=0):

        self.freq = freq
        self.speaker = speaker
        self.vol = vol
        self.fade_ms = fade_ms
        self.sound_buff = self.get_sound_buff( freq, vol, speaker)
        self.sound = pygame.sndarray.make_sound(self.sound_buff)
        self.channel = None
        print('New Tone: ' + str(freq) + "Hz   Volume: " + str(round(100*vol)))
        

    def get_sound_buff(self, freq, vol, speaker=None):
       
        num_samples = int(round( sample_rate / float(freq) )) # samples in one period
        sound_buff = numpy.zeros((num_samples,2), dtype=numpy.int16)
        volume = int(round((2 ** (bits -1) -1) * vol ))
        
        for sample in range(num_samples):
            t = float(sample)/sample_rate
            
            sine = sine_t(volume, t, freq)
            
            if speaker == 'r':
                sound_buff[sample][1] = sine
            if speaker == 'l':
                sound_buff[sample][0] = sine
            else:
                sound_buff[sample][1] = sine
                sound_buff[sample][0] = sine
        return sound_buff
    
    def get_frequency(self):
        return self.freq
    
    def get_volume(self):
        return self.vol
    
    def set_volume(self, volume):
        self.sound.set_volume(volume)
        print('Volume: %2.2f' % (volume * 100.0))
        return 

    def play(self):
        self.sound.play(-1, fade_ms = self.fade_ms)
        
    def play_cycles(self, num_cycles):
        self.channel = self.sound.play(num_cycles-1, fade_ms = self.fade_ms)
        return self.channel

    def stop(self):
        print('Tone Stopped')
        if ( self.fade_ms > 0):
            self.sound.fadeout(self.fade_ms)
            return
        self.sound.stop()