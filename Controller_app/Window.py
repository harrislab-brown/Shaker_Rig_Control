#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 16:26:04 2022

@author: eli
"""
import pygame
import pygame_gui

WIDTH, HEIGHT = 1000, 500


class Window:
    
    def __init__(self, display):
        self.display = display #pygame.display
        self.setup_ui()
        self.plot_area = (350,50,600,400)

        self.font = pygame.font.Font('./roboto/Roboto-Regular.ttf', 20)
        self.update_accel_text(0,0,0,0,True,0)
        self.update()
    
    def get_plot_area(self):
        return self.plot_area
    
    def get_screen(self):
        return self.screen

    def get_ui_manager(self):
        return self.ui_manager
    
    def get_display(self):
        return self.display

    def update(self):
        self.screen.blit(self.x_text[0], self.x_text[1])
        self.screen.blit(self.y_text[0], self.y_text[1])
        self.screen.blit(self.z_text[0], self.z_text[1])
        self.screen.blit(self.t_text[0], self.t_text[1])
        self.screen.blit(self.p_text[0], self.p_text[1])
        

    def update_accel_text(self,x_accel,y_accel,z_accel, target_accel, output_stable, percent_error):
        center_y = self.plot_area[1] + 385
        
        x_text = self.font.render('X": %5.3f' % (x_accel/100.0), True, 'red')
        y_text = self.font.render('Y": %5.3f' % (y_accel/100.0), True, 'green')
        z_text = self.font.render('Z": %5.3f' % (z_accel/100.0), True, 'blue')
        t_text = self.font.render('Z" target: %3.3f' % (target_accel), True, 'purple')
        percent_color = 'red'
        if(output_stable):
            percent_color = 'green'
        p_text = self.font.render('ERR: %3.2f%%' % (percent_error), True, percent_color)

        x_text_rect = x_text.get_rect()
        x_text_rect.center = self.plot_area[0] + 50,center_y
        self.x_text = (x_text, x_text_rect)
        
        y_text_rect = y_text.get_rect()
        y_text_rect.center = self.plot_area[0] + 150, center_y
        self.y_text = (y_text, y_text_rect)
        
        z_text_rect = z_text.get_rect()
        z_text_rect.center = self.plot_area[0] + 250, center_y
        self.z_text = (z_text, z_text_rect)

        t_text_rect = t_text.get_rect()
        t_text_rect.center = self.plot_area[0] + 375, center_y
        self.t_text = (t_text, t_text_rect)

        p_text_rect = p_text.get_rect()
        p_text_rect.center = self.plot_area[0] + 525, center_y
        self.p_text = (p_text, p_text_rect)

    def record_label_on(self):
        record_label = self.font.render('REC.', True, 'white','red')
        record_label_rect = record_label.get_rect()
        record_label_rect.center = 175,450
        self.screen.blit(record_label, record_label_rect)

    def record_label_off(self):
        record_label = self.font.render('REC.', True, 'white','white')
        record_label_rect = record_label.get_rect()
        record_label_rect.center = 175,450
        self.screen.blit(record_label, record_label_rect)


    def setup_ui(self):
        self.screen = self.display.set_mode([WIDTH, HEIGHT])
        self.screen.fill("white")
        self.display.set_caption('Harris Lab Shaker Control')
        self.ui_manager = pygame_gui.UIManager((WIDTH,HEIGHT))
       
        self.freq_input_line = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((50,80),(250,40)), manager=self.ui_manager, object_id='#frequency_input' )
        self.amp_input_line = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((50,180),(250,40)), manager=self.ui_manager, object_id='#amplitude_input' )
        self.seq_path_input_line = pygame_gui.elements.UITextEntryLine(relative_rect=pygame.Rect((50,330),(250,40)), manager=self.ui_manager, object_id='#seq_path_input')

        self.label_freq = pygame_gui.elements.UILabel(relative_rect=(pygame.Rect(50,30,200,40)), text='Input Frequency (Hz)', manager=self.ui_manager)
        self.label_amp = pygame_gui.elements.UILabel(relative_rect=(pygame.Rect(50,130,200,40)), text='Input Amplitude (G)',manager=self.ui_manager)
        self.label_seq_path = pygame_gui.elements.UILabel(relative_rect=pygame.Rect(50,280,200,40), text='Tone Sequence File Path', manager=self.ui_manager)    
            
        self.button_play = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50,230),(100,40)), text="Play", manager=self.ui_manager)
        self.button_pause = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((200,230),(100,40)), text="Pause", manager=self.ui_manager)
        self.button_play_seq = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50,380),(250,40)), text='Start Sequence', manager=self.ui_manager)
        self.button_start_save = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((50,430),(100,40)), text="Start Rec.", manager=self.ui_manager)
        self.button_stop_save = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((200,430),(100,40)), text="Stop Rec.", manager=self.ui_manager)
