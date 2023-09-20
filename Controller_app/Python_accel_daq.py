#!/usr/bin /env python

from threading import Thread
import serial
import time
import collections
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import struct
import copy
import numpy as np
import pandas as pd


class serialPlot:
    def __init__(self, serialPort='/dev/ttyUSB0', serialBaud=38400, plotLength=100, dataNumBytes=2, numPlots=1):
        self.port = serialPort
        self.baud = serialBaud
        self.plotMaxLength = plotLength
        self.dataNumBytes = dataNumBytes
        self.numPlots = numPlots
        self.rawData = bytearray(numPlots * dataNumBytes)
        self.dataType = None
        print(self.port)
        if dataNumBytes == 2:
            self.dataType = 'h'     # 2 byte integer
        elif dataNumBytes == 4:
            self.dataType = 'f'     # 4 byte float
        self.data = []
        for i in range(numPlots):   # give an array for each type of data and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
        self.isRun = True
        self.isReceiving = False
        self.thread = None
        self.plotTimer = 0
        self.previousTimer = 0
        self.buff_length = 100_000
        self.accel_buff = np.zeros((self.buff_length,self.numPlots))
        self.prev_accel_buff = np.zeros((self.buff_length,self.numPlots))
        self.prev_accel_buff_ready = False
        self.csv_written = False
        self.accel_buff_index = 0
        self.accel_buff_max = [0]*4
        self.accel_buff_min = [0]*4
        

        print('Trying to connect to: ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        try:
            self.serialConnection = serial.Serial(serialPort, serialBaud, timeout=4)
            print('Connected to ' + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
        except:
            print("Failed to connect with " + str(serialPort) + ' at ' + str(serialBaud) + ' BAUD.')
            
            
    def readSerialStart(self):
        if self.thread == None:
            self.thread = Thread(target=self.backgroundThread)
            self.thread.start()
            # Block till we start receiving values
            while self.isReceiving != True:
                time.sleep(0.1)

    def getSerialData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        privateData = copy.deepcopy(self.rawData[:])    # so that the 3 values in our plots will be synchronized to the same sample time
        
        for i in range(self.numPlots):
            data = privateData[(i*self.dataNumBytes):(self.dataNumBytes + i*self.dataNumBytes)]
            value,  = struct.unpack(self.dataType, data)
            
            self.data[i].append(value)    # we get the latest data point and append it to our array
            lines[i].set_data(range(self.plotMaxLength), self.data[i])
            
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(value))

    def get_accel_data(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        privateData = copy.deepcopy(self.rawData[:])    # so that the 3 values in our plots will be synchronized to the same sample time
        if(self.prev_accel_buff_ready == False):
            return

        self.prev_accel_buff_ready = False
        self.accel_buff_max = np.amax(self.prev_accel_buff,0)
        self.accel_buff_min = np.amin(self.prev_accel_buff,0)
        for i in range(self.numPlots):
            #data = privateData[(i*self.dataNumBytes):(self.dataNumBytes + i*self.dataNumBytes)]
            #value,  = struct.unpack(self.dataType, data)
            #self.accel_buff_max = np.amax(self.prev_accel_buff[:][i])
            #self.accel_buff_min = np.amin(self.prev_accel_buff[:][i])
            print(str(i)+' min: ' + str(self.accel_buff_min[i]) + ' max: '+str(self.accel_buff_max[i]))

            value = (self.accel_buff_max[i] - self.accel_buff_min[i]) * 10 # 100 counts / g -> 1000 counts / g
            value *= 0.5 # pk-pk acceleration / 2 to get amplitude?

            self.data[i].append(value)    # we get the latest data point and append it to our array
            lines[i].set_data(range(self.plotMaxLength), self.data[i])
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(value))
            
            
        
    def backgroundThread(self):    # retrieve data
        file = open('test_data.csv','w')
        time.sleep(1.0)  # give some buffer time for retrieving data
        self.serialConnection.reset_input_buffer()
        print('printing from inside background thread')
        while (self.isRun):
            self.serialConnection.readinto(self.rawData)
            self.isReceiving = True
            # can run either backgroundDAQ() or background_buffer(), but not both!
            self.backgroundDAQ(file) 
            #self.background_buffer()
        file.close()


    def backgroundDAQ(self,file):
        privateData = copy.deepcopy(self.rawData[:])
        if self.accel_buff_index == self.buff_length and self.csv_written == False:
            print('buffer full. writing to csv')
            self.accel_buff_index = 0
            pd.DataFrame(self.accel_buff).to_csv('./data/freq_50_vol_100.csv',header=None, index=None)
            self.close()
            self.csv_written = True
            
        for i in range(self.numPlots):
            data = privateData[(i*self.dataNumBytes):((i+1)*self.dataNumBytes)]
            value, = struct.unpack(self.dataType, data)
            self.accel_buff[self.accel_buff_index][i] = value
        self.accel_buff_index += 1

    def background_buffer(self):
        if self.accel_buff_index == self.buff_length:
            self.prev_accel_buff = self.accel_buff
            self.accel_buff = np.zeros((self.buff_length,self.numPlots))
            self.accel_buff_index = 0
            self.prev_accel_buff_ready = True

        privateData = copy.deepcopy(self.rawData[:])
        for i in range(self.numPlots):
            data = privateData[(i*self.dataNumBytes):((i+1)*self.dataNumBytes)]
            value, = struct.unpack(self.dataType, data)
            self.accel_buff[self.accel_buff_index][i] = value
        self.accel_buff_index += 1


    def close(self):
        self.isRun = False
        self.thread.join()
        self.serialConnection.close()
        print('Disconnected...')


def main():
    # portName = 'COM5'
    portName = '/dev/ttyACM1'
    baudRate = 2000000
    maxPlotLength = 50     # number of points in x-axis of real time plot
    dataNumBytes = 2        # number of bytes of 1 data point
    numPlots = 4            # number of plots in 1 graph
    s = serialPlot(portName, baudRate, maxPlotLength, dataNumBytes, numPlots)   # initializes all required variables
    s.readSerialStart()                                               # starts background thread

    # plotting starts below
    pltInterval = 40    # Period at which the plot animation updates [ms]
    xmin = 0
    xmax = maxPlotLength
    ymin = -1000
    ymax = 1000
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(xlim=(xmin, xmax), ylim=(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10)))
    ax.set_title('Shaker Rig Accelerometer')
    ax.set_xlabel("Time")
    ax.set_ylabel("Accelerometer Output (mG)")
    plt.grid(True)

    lineLabel = ['X', 'Y', 'Z','dT']
    style = ['r-', 'c-', 'b-','g-']  # linestyles for the different plots
    timeText = ax.text(0.70, 0.95, '', transform=ax.transAxes)
    lines = []
    lineValueText = []
    for i in range(numPlots):
        lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
        lineValueText.append(ax.text(0.70, 0.90-i*0.05, '', transform=ax.transAxes))
    anim = animation.FuncAnimation(fig, s.getSerialData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
    #anim = animation.FuncAnimation(fig, s.get_accel_data, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple

    plt.legend(loc="upper left")
    plt.show()
    
    s.close()


if __name__ == '__main__':
    main()
