from threading import Thread
import serial
import struct
import copy
import numpy as np
import time

class Serial_Monitor:
    def __init__(self,serial_port='COM6',serial_baud=2000000, num_data_bytes = 2, num_traces = 1, buff_len = 666):
        self.port = serial_port
        self.baud = serial_baud
        self.num_data_bytes = num_data_bytes
        self.num_traces = num_traces
        self.buff_len = buff_len
        self.raw_data = bytearray(num_data_bytes * num_traces)
        self.data_type = None
        if num_data_bytes == 2:
            self.data_type = 'h'
        elif num_data_bytes == 4:
            self.data_type = 'f'
        self.data_buff = np.zeros((self.buff_len, self.num_traces))
        self.prev_data_buff = np.zeros((self.buff_len,self.num_traces))
        self.data_buff_ready = False
        self.data_buff_index = 0
        self.is_run = True
        self.is_receiving = False
        self.thread = None
        self.plot_timer = 0
        self.prev_timer = 0

        print('Trying to connect to: ' + str(serial_port) + ' at ' + str(serial_baud) + ' BAUD.')
        try:
            self.serial_connection = serial.Serial(serial_port, serial_baud, timeout=4)
            print('Connected to ' + str(serial_port) + ' at ' + str(serial_baud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serial_port) + ' at ' + str(serial_baud) + ' BAUD.')

    def serial_input_background_init(self):
        if self.thread == None:
            self.thread = Thread(target = self.background_thread)
            self.thread.start()
            while self.is_receiving != True:
                time.sleep(0.1) # wait until background thread starts receiving data

    def background_thread(self):
        time.sleep(1)
        self.serial_connection.reset_input_buffer()
        while( self.is_run):
            self.serial_connection.readinto(self.raw_data)
            self.is_receiving = True

            if self.data_buff_index == self.buff_len - 1:
                self.prev_data_buff = np.copy(self.data_buff)
                self.data_buff_index = 0
                self.data_buff_ready = True
            
            private_data = copy.deepcopy(self.raw_data[:])
            for i in range(self.num_traces):
                data = private_data[(i * self.num_data_bytes) : ((i+1) * self.num_data_bytes)]
                value, = struct.unpack(self.data_type, data)
                self.data_buff[self.data_buff_index][i] = value
            self.data_buff_index += 1

    def buff_is_ready(self):
        return self.data_buff_ready

    def get_buffer(self):
        self.data_buff_ready = False
        return self.prev_data_buff # else, return prev_data_buff: copy of data_buff when it was last full
    
    def serial_write(self,val):
        val = int(round(val))
        val_str = bytes(str(val), 'utf-8')
        print(val_str)
        self.serial_connection.write(val_str)

    def close(self):
        self.is_run = False
        self.thread.join()
        self.serial_connection.close()
        print('Serial Disconnected')