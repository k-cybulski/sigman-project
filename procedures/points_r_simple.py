import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""
Procedure applying a simple algorithm to find R points on an ECG
waveform. It searches for the highest values of the window integral
over the squared derivative, and selects the highest value of the 
waveform within them.
""")
author = 'kcybulski'
arguments = {
    'threshold_fraction':("Threshold of the window integral over which "
                          "the waveform itself is considered."),
    'threshold_period':("Period in which the threshold is calculated "
                        "based on `threshold_fraction`*maximum value "
                        "of the integral."),
    'safe_period':"Period in which two Rs cannot be found."}
default_arguments = {
    'threshold_fraction':0.7,
    'threshold_period':2,
    'safe_period':0.25}
output_type = 'r'
required_waves = ['ecg']
required_points = []

def interpret_arguments(waves, points, arguments):
    output_arguments = {}
    for key, item in arguments.items():
        try:
            output_arguments[key] = float(item)
        except:
            raise InvalidArgumentError("{} is invalid.".format(arguments[key]))
    return output_arguments

def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['ecg']
    
    sample_length = wave.sample_length
    data = wave.data_slice(begin_time, end_time)
    data = np.array(data)

    derivative = [0] * 2
    for i in range(2,len(data)-2):
        derivative.append(( (1/8) * (-data[i-2]-2*data[i-1]+2*data[i+1]+data[i+2]) )**2)
    derivative = derivative + [0] * 2
    derivative = np.array(derivative)

    window_width = 0.15/sample_length # 150 ms
    half_window = int(window_width/2) 
    integral = [0]  * half_window 
    for i in range(half_window, len(derivative)-half_window):
        integral.append(np.sum(derivative[i-half_window:i+half_window]))
    integral = integral + [0] * half_window
    integral = np.array(integral)
    
    threshold = np.max(integral[0:int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
    r_x = []
    r_y = []
    begin_i = 0
    average_period = 0
    i = 0
    while i < len(integral):
        if integral[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(r_x)==0 or i*sample_length > r_x[-1] + settings['safe_period'] - begin_time:
                    hopeful_slice = data[begin_i:i]
                    maximum_i = np.argmax(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    r_x.append(begin_time+sample_length*(fin_i-1))
                    r_y.append(data[fin_i])
                    threshold = np.max(integral[fin_i:fin_i+int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
                    begin_i = 0
                    if len(r_x) > 3:
                        average_period = ( (r_x[-1]-r_x[-2]) + (r_x[-2]-r_x[-3]) + (r_x[-3]-r_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > r_x[-1] + average_period*1.7:
                threshold *= 0.6
                i = int((r_x[-1]+settings['safe_period'])/sample_length)
        i += 1
    r_x = np.array(r_x)
    return r_x, r_y

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)
