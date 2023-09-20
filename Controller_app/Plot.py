#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  8 16:34:51 2022

@author: eli
"""
import pygame
import random
import math
import numpy as np

class Plot:
    
    def __init__(self, screen, x, y, width, height):
        # x bounds are between 0 and width
        # y bounds are between -height/2 and height/2
        self.plot_area = (x,y,width,height)
        self.screen = screen
        self.plt_width = width
        self.plt_height = height
        self.plt_offset = [x,y]
        self.x_scale = 1.5
        self.y_scale = 1
        self.total_time = 0 
        self.x_pix_per_sec = 50.0        

        self.Y_MIN = -500
        self.Y_MAX = 500
        self.ACCEL_Y_OFFSET = -400
        
        self.plt_grid = True
        self.plt_padding = 5

        self.ax_queue = []
        self.ay_queue = []
        self.az_queue = []
        self.at_queue = []

        self.num_points_x = math.floor(self.plt_width / self.x_scale)
        self.init_frames()

    def update(self, time_delta):
        self.total_time += time_delta
        self.draw_background()

        self.update_trace('ax')
        self.update_trace('ay')
        self.update_trace('az')
        self.update_trace('at')
        
        self.update_frame(self.ax_frame, 'red')
        self.update_frame(self.ay_frame, 'green')
        self.update_frame(self.az_frame, 'blue')
        self.update_frame(self.tg_frame, 'purple')


    def draw_background(self):
         pygame.draw.rect(self.screen,'grey',self.plot_area)
         num_vert_lines =  10
         num_hori_lines = 10
         if self.plt_grid:
             for i in range(num_vert_lines+1):
                 y_val = i * self.plt_height/num_vert_lines
                 self.draw_line((120,120,120),0,y_val,self.plt_width,y_val )
             for i in range(num_hori_lines+1):
                 x_val = i * self.plt_width/num_hori_lines
                 self.draw_line((120,120,120),x_val,0,x_val,self.plt_height )
                 
    
    def add_data_frame(self,frame):
        self.init_frames()
        trig_index = 1
        trig_found = False

        while (trig_found == False):
            # camera trigger is frame[:,4], use camera trigger as start of plot
            if( frame[trig_index][4] > frame[trig_index-1][4]):
                trig_found = True
            if( trig_index == self.num_points_x-1):
                trig_found = True
                trig_index = 0
            trig_index += 1
        
        for i in range(self.num_points_x):
            if i + trig_index >= len(frame):
                data_pt = [0,0,0,0,0]
            else:
                data_pt = frame[i+trig_index]
            self.ax_frame[i] = [i * self.x_scale, data_pt[0]]
            self.ay_frame[i] = [i * self.x_scale, data_pt[1]]
            self.az_frame[i] = [i * self.x_scale, data_pt[2]]
            self.tg_frame[i] = [i * self.x_scale, (data_pt[4] * 100 - 50)]


    def add_frame(self, trace, data_buff):
        if trace == 'ax':
            self.ax_frame = data_buff
        if trace == 'ay':
            self.ay_frame = data_buff
        if trace == 'az':
            self.az_frame = data_buff
        if trace == 'dt':
            self.dt_frame = data_buff

    def update_frame(self, frame, color):
        line_queue = []
        for elem in frame:
            point = self.coord_to_pixel(elem)
            line_queue.append(point)

        if len(line_queue)>=2:
            pygame.draw.aalines(self.screen, color, False ,line_queue)
        

    def add_point(self, trace, x, y):
        if trace == 'ax':
            queue = self.ax_queue
        if trace == 'ay':
            queue = self.ay_queue
        if trace == 'az':
            queue = self.az_queue
        if trace == 'at':
            queue = self.at_queue
        queue.append((x,y + self.ACCEL_Y_OFFSET))
    

    def draw_trace(self, queue, color):
        pix_queue = []
        x_time_offset = (self.total_time * self.x_pix_per_sec)
        pop_list = []
         # calculate pixel x,y location from absolute x,y coordinate. Only plot points within the plotting region
        for i in range(len(queue)):
            pix_point = self.coord_to_pixel(queue[i])
            pix_point[0]= pix_point[0] + self.plt_width + (queue[i][0] * self.x_pix_per_sec) - (x_time_offset + self.plt_padding) - queue[i][0]
            if (self.plt_offset[0]+self.plt_padding)<pix_point[0] and (self.plt_offset[1]+self.plt_padding)<pix_point[1] and pix_point[1]<(self.plt_offset[1]+ self.plt_height-self.plt_padding):
                pix_queue.append(pix_point)
            else:
                pop_list.append(queue[i])
        for point in pop_list:
            queue.remove(point)

        # for point in pix_queue:
        #     pygame.draw.circle(self.screen, color, point, 3)
        if len(pix_queue)>=2:
            pygame.draw.aalines(self.screen, color, False ,pix_queue)

        
    def update_trace(self,trace):
        if trace == 'ax':
            self.draw_trace(self.ax_queue,'red')
            return self.ax_queue
        if trace == 'ay':
            self.draw_trace(self.ay_queue, 'green')
            return self.ay_queue
        if trace == 'az':
            self.draw_trace(self.az_queue, 'blue')
            return self.az_queue
        if trace == 'at':
            self.draw_trace(self.at_queue, 'purple')
    

        
    def coord_to_pixel(self,point):
        pix_x = self.plt_offset[0] + point[0]
        y_scaled = (point[1]-self.Y_MIN) / (self.Y_MAX-self.Y_MIN)
        pix_y = self.plt_offset[1] + self.plt_height - (y_scaled * self.plt_height)
        return [pix_x, pix_y]
    
    
    def coords_to_pixels(self, coord_queue):
        pix_queue = []
        x_pix_offset = self.total_time * self.x_pix_per_sec
        pop_list=[]
        for i in range(len(coord_queue)):
            point = coord_queue[i]
            
            pix_y = self.coord_to_pixel(point)[1]
            
            pix_x = self.plt_width + self.plt_offset[0] + (point[0] * self.x_pix_per_sec) - x_pix_offset - self.plt_pading
            if pix_x > self.plt_offset[0] + self.plt_padding:
                pix_queue.append([pix_x, pix_y])
            else:
                pop_list.append(coord_queue[i])
        for point in pop_list:    
            coord_queue.remove(point)
        return pix_queue

    def draw_line(self, color, x1,y1,x2,y2):
        pygame.draw.line(self.screen, color, (self.plt_offset[0]+ x1,self.plt_offset[1]+self.plt_height-y1),(self.plt_offset[0]+ x2,self.plt_offset[1]+self.plt_height-y2))

    def init_frames(self):
        self.ax_frame = np.zeros([self.num_points_x,2])
        self.ay_frame = np.zeros([self.num_points_x,2])        
        self.az_frame = np.zeros([self.num_points_x,2])
        self.dt_frame = np.zeros([self.num_points_x,2])
        self.tg_frame = np.zeros([self.num_points_x,2])