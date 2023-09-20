import numpy as np
from scipy import fft, signal
from numpy import mean, std



class Filter:
    def __init__(self, freq, sample_rate, buff_len, num_traces, threshold):
        self.freq = freq
        self.sample_rate = sample_rate
        self.buff_len = buff_len
        self.num_traces = num_traces
        self.threshold = threshold

        self.nyquist_freq = self.sample_rate / 2
        self.cutoff_multiplier = 5
        self.input_buff = np.zeros((num_traces, buff_len))
        self.output_buff = np.zeros((num_traces, buff_len))

        self.init_filter(self.freq * self.cutoff_multiplier)


    def init_filter (self, cutoff_freq):
        self.cutoff_freq = cutoff_freq
        Wn = self.cutoff_freq / self.nyquist_freq
        self.filter_arg_b, self.filter_arg_a = signal.butter( 3, Wn, 'lowpass')


    def set_freq(self, freq):
        self.freq = freq
        self.init_filter(self.freq, self.freq * self.cutoff_multiplier)


    def apply_filter(self, data_buff):
        # Applies the filter to data_buff. Sets output_buff object variable to filtered data, which is used by later methods
        # apply filter to a different data frame to process next batch of data
        self.input_buff = np.asarray(data_buff)
        self.output_buff = signal.filtfilt(self.filter_arg_b, self.filter_arg_a, self.input_buff)
        return self.output_buff
        
        #for i in range(len(self.input_buff[:])):
        #    self.output_buff[i] = signal.filtfilt(self.filter_arg_b, self.filter_arg_a, self.input_buff[i])
        #return self.output_buff

    def find_average_accel(self):
        cycle_list = []
        trigger_list = []
        accel_list = []
        trigger_index = 0
        thresh = (max(self.output_buff[15:-15]) + min(self.output_buff[15:-15])) * 0.5

        for i in range(1,len(self.output_buff)):
            if((self.output_buff[i-1] < thresh) and (self.output_buff[i] >= thresh)):
                cycle = self.output_buff[trigger_index:i-1]
                cycle_list.append(cycle)
                trigger_index = i
                trigger_list.append(i)
            
        for i in range(1,len(cycle_list)-1):
            a_max = max(cycle_list[i])
            a_min = min(cycle_list[i])
            accel_list.append((a_max - a_min)/2)
        if (len(accel_list) >0):
            return mean(accel_list),std(accel_list)
        else:
            return 0,0

    def find_thd(slef):
        pass