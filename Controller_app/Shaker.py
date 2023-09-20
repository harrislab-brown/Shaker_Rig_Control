#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 14:45:10 2022

@author: eli
"""

from Tone import Tone
from Window import Window
from Plot import Plot
from Serial_Monitor import Serial_Monitor
from Filter import Filter

import pygame
import pygame_gui
from time import sleep
from datetime import datetime
import threading
import serial
import numpy as np

bits = 16
sample_rate = 44100
"""
###
adjust the load_tone new tone volume, Kp and Ki to get good responsiveness and resolution within the desired measurement range
###
"""

class Shaker:
    """
    Top level object. Runs the main loop for plotting and getting new data from accelerometers.
    Shaker contains: 
        -Tone: sound that is played through the shaker
        -Window: the system window with layout and GUI elements
        -Plot: pixel based canvas within Window, used to plot data
        -Serial_Monitor: real time communication with microcontroller to relay accel data
        -Filter: data processing functions for real time accel data
    """
    def __init__(self):
        self.game = pygame.init()
        pygame.mixer.init(sample_rate,bits)
        self.clock = pygame.time.Clock()
        self.display = pygame.display
        
        self.max_vol = 1
        self.run_open_loop = False

        self.init_tone()
        self.init_window()
        self.init_plot()
        self.init_serial_monitor()
        self.run_serial_monitor = True # set to true if using a microcontroller, false for testing
        if self.run_serial_monitor:
            self.serial_monitor.serial_input_background_init()
        self.init_filter()
        self.init_control_loop()
        
        self.total_time = 0
        self.plot_trig = False # false will stream data left to right, true will show snapshots alligned by trigger condition
        self.plot_num_points = 100

        self.stream_data = False
        self.output_path = '../data/' 
        self.output_file = None
        self.stream_raw_output = True
        
        

        ### begin update loop ###
        self.run = True
        self.update_loop()


    def update_loop(self):
        ### update state of displayed information, runs 120 times per second ###
        while self.run:
            time_delta = self.clock.tick(120)/1000

            for event in pygame.event.get():
                self.window_ui_manager.process_events(event)

                # close window if clicked (x)
                if event.type == pygame.QUIT:
                    self.run = False
                    if self.run_serial_monitor:
                        self.serial_monitor.close()
                    self.exit()

                # get info from text entry boxes
                if (event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_object_id == '#frequency_input'):
                    self.set_tone_frequency(float(event.text))    
                if (event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_object_id == '#amplitude_input'):
                    self.set_accel_amplitude(float(event.text))
                if (event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED and event.ui_object_id == '#seq_path_input'):
                    self.path = event.text
                    self.load_tone_sequence(self.path)

                # Change state of tone being played based on UI button click
                if (event.type == pygame_gui.UI_BUTTON_PRESSED):
                    if (event.ui_element == self.window.button_play):
                        print('Play Pressed')
                        self.play_tone()
                    if (event.ui_element == self.window.button_pause):
                        print('Pause Pressed')
                        self.pause_tone()
                    if (event.ui_element == self.window.button_play_seq):
                        ### changed for luke to do accel sweeps! ###
                        print('Play Sequence Pressed')
                        print('beginning accel sweep from 0.8G - 2G, 12 stepps, 2 sec per step')
                        ### FOR LUKE: change accel sweep ###
                        self.start_accel_sweep(0.2, .8, 21, 8, 1)
                        #self.play_sequence()
                    if (event.ui_element == self.window.button_start_save):
                        print('Start Logging Acceleration Data')
                        self.start_stream_to_csv()
                    if (event.ui_element == self.window.button_stop_save):
                        print('Stop Logging Acceleration Data')
                        self.stop_stream_to_csv()
            # If we expect to have a microcotroller connected, get new serial data
            if self.run_serial_monitor:
                self.update_serial_monitor(time_delta)
                
            # Update display with new info
            self.window_ui_manager.update( time_delta )
            self.plot.update( time_delta )
            self.window.update()
            self.window_ui_manager.draw_ui(self.window_screen)
            pygame.display.update() 
        # when (x) is clicked, exit update loop
        pygame.quit()
    
    
    def update_serial_monitor(self, time_delta):
        # get most recent serial data
        self.total_time += time_delta

        if self.serial_monitor.buff_is_ready():
            # only plotting the last received data point. Data array can have many points
            data = self.serial_monitor.get_buffer()

            x_out = self.x_filter.apply_filter(data[:,0])
            y_out = self.y_filter.apply_filter(data[:,1])
            z_out = self.z_filter.apply_filter(data[:,2])
            
            # plot lp-filtered data trace or raw data trace:
            #self.plot.add_data_frame(data)
            plot_arr = np.transpose(np.asarray([x_out,y_out,z_out,data[:,3],data[:,4]]))
            self.plot.add_data_frame(plot_arr)
            
            self.x_accel,x_accel_std = self.x_filter.find_average_accel()
            self.y_accel,y_accel_std = self.y_filter.find_average_accel()
            self.z_accel,z_accel_std = self.z_filter.find_average_accel()
            self.plot.add_point('ax', self.total_time, self.x_accel)
            self.plot.add_point('ay', self.total_time, self.y_accel)
            self.plot.add_point('az', self.total_time, self.z_accel)
            self.plot.add_point('at', self.total_time, self.target_accel*100)
            self.window.update_accel_text(self.x_accel, self.y_accel, self.z_accel, self.target_accel, self.hold_output, self.percent_error)
            if(self.tone_running and not self.run_open_loop):
                self.update_control_loop(self.target_accel, time_delta)

            #print('Average Accel: (G)')
            #print('X: %5.3f Y: %5.3f Z: %5.3f' % (self.x_accel/100,self.y_accel/100,self.z_accel/100))
            #print([x_accel_std, y_accel_std, z_accel_std])
            if( self.stream_data == True ):
                curr_time = datetime.now().strftime('%H-%M-%S.%f')[:-3]
                if( not self.stream_raw_output):
                    csv_line = curr_time + ",%5.3f,%5.3f,%5.3f,%5.3f\n" % (self.x_accel/100,self.y_accel/100,self.z_accel/100,self.target_accel)
                    self.output_file.write(csv_line)
                else:
                    for line in data:
                        self.output_file.write(','.join(map(str, line))+'\n')
                


    def set_accel_amplitude(self, new_target_accel):
        self.target_accel = new_target_accel
        if self.run_open_loop:
            self.tone.set_volume(new_target_accel)
            self.serial_monitor.serial_write(new_target_accel)

    def update_control_loop(self, target_accel, time_delta): 
        if self.run_open_loop:
            return
        
        self.error = target_accel - (self.z_accel / 100.0)

        if(target_accel == 0):
            target_accel = 0.001

        self.percent_error  = 100 * abs(1 - ((self.z_accel/100) / target_accel))
        if(self.percent_error < 1):
            self.hold_output = True
        else:
            self.hold_output = False        
        integral = self.prev_integral
        derivative =  0
        #if( self.hold_output == False):
        if(True):
            integral += self.error * time_delta
            derivative = ( self.prev_error - self.error ) / time_delta

        output = self.k_p * self.error + self.k_i * integral + self.k_d * derivative
        self.prev_error = self.error
        if ( output < 1 and output >= 0):
            self.prev_integral = integral
        #print('percent error: %5.2f' % (self.percent_error))
        self.set_tone_volume(output)
        #print('error: %5.3f output: %5.6f' %( self.error, output))



    def init_tone(self):
        # define a starting tone, init tone var iables
        self.tone = self.load_tone(50,0.50,speaker=None)
        self.tone_running = False
        self.tone_sequence_running = False
        self.tone_sequence_path = None
        self.tone_sequence = None
        self.fade_ms = 0 # volume fade in/out, input to pygame audio library
        self.speaker = 'r' # play out of only one speaker channel 
        self.sweep_thread = None

    def init_window(self):
        # create system window and init window variables
        self.window = Window(self.display)
        self.window_plot_area = self.window.get_plot_area()
        self.window_display = self.window.get_display()
        self.window_screen = self.window.get_screen()
        self.window_ui_manager = self.window.get_ui_manager()

    def init_plot(self):
        # instantiate Plot object, including window to plot in and plot coordinates within window
        self.plot = Plot(self.window_screen, *self.window_plot_area)

    def init_serial_monitor(self):
        # instantiate serial monitor. Pass in info to decode data. Must match values expected from microcontroller
        self.buff_len = 2000
        self.serial_monitor = Serial_Monitor(num_data_bytes=2, num_traces = 5, buff_len = self.buff_len)

    def init_filter(self):
        # set up filtering of incoming data
        freq = self.tone.get_frequency()
        sample_rate = 10000
        self.x_filter = Filter(freq, sample_rate, self.buff_len, 3, 90)
        self.y_filter = Filter(freq, sample_rate, self.buff_len, 3, 0)
        self.z_filter = Filter(freq, sample_rate, self.buff_len, 3, 0)
        self.x_accel = 0.0
        self.y_accel = 0.0
        self.z_accel = 0.0

    def init_control_loop(self):
        self.target_accel = 0
        self.percent_error = 0
        self.error = 0
        self.prev_error = 0
        self.prev_integral = 0
        self.hold_output = False
        self.k_p = 0.016#0.013
        self.k_i = 1.95#1.8
        self.k_d = 0.00005


    def exit(self):
        # end of program code
        if( self.stream_data == True):
            self.stop_stream_to_csv()
        try:
            self.sweep_thread.join(timeout=1)
        except:
            pass
        print('THANKS FOR SHAKING')
    
    def load_tone(self, freq, amp, speaker=None, fade_ms=0):
        # create a new Tone object. Wrapper function to make things consistent 
        new_tone = Tone(freq, self.max_vol, speaker, fade_ms)
        new_tone.set_volume(amp)
        return new_tone
        
    def play_tone(self, tone=None):
        # If a tone can be played, play it. Will play currently loaded tone by default unles tone arg is set.
        if self.tone_sequence_running:
            print('sequence running, cannot play')
        elif self.tone_running:
            print('tone already playing')
        else:
            self.tone_running = True
            if tone==None:
                
                self.tone.play()
            else:
                tone.play()
                
    def play_sequence(self):
        # Play a sequence of tones from a tone file. Sequence is played in a separate thread.
        if self.tone_running:
            self.pause_tone()
        elif self.tone_sequence_running:
            print('sequence already running')
        else:
            if self.tone_sequence != None:
                thread = threading.Thread(target = self.play_tone_sequence)
                thread.start()
                return
            else:
                print('sequence not set')

    def start_accel_sweep(self, start_accel, stop_accel, num, hold_time, trans_time):
        accel_list = np.linspace(start_accel,stop_accel,num)
        print(accel_list)

        self.sweep_thread = threading.Thread(target = self.accel_sweep_thread, args=[accel_list,hold_time,trans_time])
        self.sweep_thread.start()
        self.set_accel_amplitude(start_accel)
        self.play_tone()

    def accel_sweep_thread(self, accel_list, hold_time, trans_time):
        for accel in accel_list:
            sleep(trans_time)
            self.set_accel_amplitude(accel)
            sleep(hold_time)
        

        
    def pause_tone(self,tone=None):
        # Pause current tone. Cannot pause a tone sequence 
        if self.tone_sequence_running:
            print('sequence running, cannot pause')
            return
        if self.tone_running == False: 
            return
        self.tone_running=False
        if tone==None:
            self.tone.stop()
        else:
            tone.stop()
                            
    def set_tone_frequency(self, frequency):
        # change frequency of currently set tone. If tone is playing, changes to frequency will stop curr
        # tone and create a new one with new frequency. Volume of new tone set to vol of old tone
        volume = self.tone.get_volume()
        if self.run_open_loop:    
            next_tone = self.load_tone(frequency, volume, speaker=None, fade_ms=0)
        else:
            next_tone = self.load_tone(frequency, volume/100, speaker=None, fade_ms=0)

        if self.tone_running:    
            self.pause_tone()
            self.tone = next_tone
            self.play_tone()
        else:
            self.tone=next_tone
        
    def set_tone_volume(self, volume, speaker=None, fade_ms=0):
        # Set volume of tone. This does not create a new tone, delay / jump in output *should* happen.
        if(volume >1):
            volume=1
        if(volume < 0):
            volume=0
        self.tone.set_volume(volume)
            
    def load_tone_sequence(self,path):
        # load in a new sequence of tones from a file. Must be in correct csv format
        self.tone_sequence = []
        try:
            file = open(path, 'r')
        except:
            print('File Not Found')
            return
        self.path = path
        for line in file:
            # tone parameters from file: freq(0), amp(1), time_sec(2) 
            tone_params = line.split(',')
            tone_params = list(map(float,tone_params)) #convert strings to floats
            num_cycles = int(round(tone_params[0] * tone_params[2]))
            tone = self.load_tone(tone_params[0], tone_params[1]/100)
            self.tone_sequence.append([tone,tone_params[2], num_cycles])
            
    def play_tone_sequence(self):
        # begin playing tone sequence
        print('begin playing tone sequence')
        self.tone_sequence_running = True
        self.tone_running = True
        
        for tone in self.tone_sequence:
            tone[0].play_cycles(tone[2])
            sleep(tone[1])        
            
        self.tone_sequence_running = False
        self.tone_running = False
        print('tone sequence complete')


    def start_stream_to_csv(self):
        if(self.stream_data == False):
            self.window.record_label_on()
            #timestr = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            timestr = datetime.now().strftime('%H-%M-%S')
            #self.output_file = open(self.output_path+'shaker_data_'+timestr+'.csv', 'x')
            self.output_file = open(self.output_path+'shaker_measurement_amp-'+str(self.target_accel)+'_freq-'+str(self.tone.get_frequency())+'_'+timestr+'.csv', 'w+')
            self.stream_data = True

    def stop_stream_to_csv(self):
        self.window.record_label_off()
        self.output_file.close()
        self.stream_data = False