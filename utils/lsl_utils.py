#from _typeshed import Self
#from textwrap import dedent
from typing import DefaultDict
import pyxdf
import numpy as np
import mne
import matplotlib.pyplot as plt

from utils.parameters import *

class LSL_to_MNE ():

    """
    creating the MNE data structute using LSL output

    Parameters
    - path (of the LSL data)
    - sfreq (sampling frequency, can either be set or automatically be detected)
    - stream_n (the LSL stream corresponding to the EEG data)
    - condition_time_points (the beginning and end of each condition in seconds, measured from the beginning of the recording)
    - epoch_length (each condition is devided in n epochs of this length (in seconds))

    The entire pipeline can be called using `lsl_to_array`, infos can always be called using `print_info(self)`
    
    """

    def __init__(self, path, verbose = True, stream_n = None, sfreq = None, scale = False, remove_DC = False):
        self.path = path 
        self.sfreq = sfreq
        self.stream_n=stream_n
        data, header = pyxdf.load_xdf(path)
        self.data = data
        self.info = None
        if stream_n == None: 
            self.get_channel_names()
        if stream_n != None:
            print('selected stream is {}'.format(self.data[self.stream_n]['info']['name']))
            self.get_real_sampling_rate(verbose = verbose)
            self.time_series = self.data[self.stream_n]['time_series']
            if scale == True:
                self.time_series = self.scale(self.time_series)
            if remove_DC == True: 
                self.time_series = self.remove_DC(self.time_series)

    def get_channel_names (self):
        self.channel_names = []
        for i in range (len(self.data)):
            name = self.data[i]['info']['name']
            self.channel_names.append(name)
            print ("Stream_n {} is channel {}".format(i, name))
        '''
        # this loop can be used if the normal output doesn't show all necessary rows 
        for i in np.linspace (22,40,23):
            name = two_EEG_all_bio.data[int(i)]['info']['name']
            print ("Dict entry number {} is {}".format(int(i), name))
        '''

    def scale (self, input_array, scaling_factor = 10**6):
        '''
        scales EEG data by a factor of 10e6 to fit the MNE data structure
        '''
        output_array = input_array / scaling_factor
        return (output_array)

    def remove_DC (self, input_array, axis=0):
        '''
        takes a numpy array as input and removes the average of each vector amongst either axis
        '''
        average = np.average(input_array, axis=0)
        output_array = input_array - average
        return (output_array)

    def make_raw (self, info = None, verbose = False, bounds = None):
        if self.info == None: 
            self.create_info()
        if self.time_series.shape[0] > self.time_series.shape[1]:
            data = self.time_series.T
        else: 
            data = self.time_series
        if bounds != None:
            data = data [:,bounds[0]:bounds[1]]

        self.raw = mne.io.RawArray(data, self.info)
        ten_twenty_montage = mne.channels.make_standard_montage('standard_1020')
        self.raw.set_montage(ten_twenty_montage)

        if verbose == True: 
            self.raw.plot(show_scrollbars=False, show_scalebars=False)
            print(self.raw)
            print(self.raw.info)        

    def make_epochs (self, condition_time_points = np.array(((5, 25), (35, 55), (65,85), (95,115))), epoch_length = 1, verbose=False):
        '''
        inputs: 
            self.time_series: must be assiged prior by using the "scale" funciton 
            condition_time_poitns [s]: array of tuples. First instance of each tuple is the beginning of a condition in seconds, second instance the end 
            epch_length [s]: length of epochs that each condition will be split into (in seconds)
        based on this MNE tutorial: https://mne.tools/stable/auto_tutorials/simulation/10_array_objs.html
        '''   
        if self.info == None: 
            self.create_info()     

        self.epo = {}
        condition_blocks = condition_time_points * self.sfreq
        epoch_length_samples = epoch_length * self.sfreq

        for j in range (len (condition_blocks)):
            epoch_boundaries = np.vstack((np.arange(condition_blocks[j][0],condition_blocks[j][1],epoch_length_samples), np.arange(condition_blocks[j][0],condition_blocks[j][1],epoch_length_samples)+500)).T
            for i in range(len(epoch_boundaries)):
                start = int (epoch_boundaries[i,0])
                end = int(epoch_boundaries[i,1])
                if i > 0:
                    new_epoch_array = self.time_series[start:end,:].T[np.newaxis,:, :]
                    epoch_array = np.append(epoch_array,new_epoch_array,0)
                else:
                    epoch_array = self.time_series[start:end,:].T[np.newaxis,:, :]
                    np.datetime_data
            self.epo["epo{}".format(j)] = mne.EpochsArray(epoch_array, self.info)

    def create_info (self, ch_names = ch_names_bitbrain):
        n_channels = min (self.time_series.shape)
        ch_types = ['eeg']*n_channels
        self.info = mne.create_info(ch_names, ch_types=ch_types, sfreq=self.sfreq)

    def get_real_sampling_rate (self, verbose = False):
        '''
        this function returns the sampling rate based on the time difference between point 'timepoint' and the next point
        input: 
            stream_n: 
            data: data imported through lab streaming layer
        '''
        step_size = (self.data[self.stream_n]['time_stamps'][1:] - self.data[self.stream_n]['time_stamps'][:-1])
        step_size = np.round(step_size,5)
        mean =np.mean(step_size)
        variance = np.var(step_size)
        real_sfreq = 1/mean
        real_sfreq_rounded = np.round (1/mean,0)
        print ('mean step size is {}'.format(mean))
        print ('variance of step size is {}'.format(variance))
        print ('average sampling rate is {}'.format (real_sfreq))
        print ('assigned sampling rate is {}'.format (real_sfreq_rounded))
        self.sfreq = real_sfreq_rounded

        if verbose == True:    
            plt.plot(1/step_size)
            plt.title('sampling rate over time')
            plt.xlabel('sample number')
            plt.ylabel('sampling rate [Hz]')
            plt.show()
    
    def print_info(self):
        '''
        prints the 
        '''    
        print ('import path is {}'.format(self.path))
        print ('sfreq is {}'.format (self.sfreq))
        print ('selected strem_n is {}'.format(self.stream_n))
        print ('the condition timepoints are {}'.format (self.condition_time_points))
        print ('the epoch length is {} seconds'.format (self.epoch_length))
