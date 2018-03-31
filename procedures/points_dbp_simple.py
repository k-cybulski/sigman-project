from sigman import analyzer 
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""
Procedure applying a simple algorithm to find DBP points on a BP
waveform. It searches for the lowest values of the window integral
over the derivative, and selects the lowest value of the waveform
within them.
""")
author = 'kcybulski'
arguments = {
    'threshold_fraction':("Threshold of the window integral over which "
                          "the waveform itself is considered."),
    'threshold_period':("Period in which the threshold is calculated "
                        "based on `threshold_fraction`*maximum value "
                        "of the integral."),
    'safe_period':"Period in which two DBPs cannot be found."}
default_arguments = {
    'threshold_fraction':0.4,
    'threshold_period':2,
    'safe_period':0.25}
output_type = 'dbp'
required_waves = ['bp']
required_points = []

def interpret_arguments(waves, points, arguments):
    output_arguments = {}
    for key, item in arguments.items():
        try:
            output_arguments[key] = float(item)
        except:
            raise InvalidArgumentError("{} is invalid.".format(arguments[key]))
    return output_arguments

def procedure(waves, points, begin_time, end_time, arguments):
    wave = waves['bp']
    
    sample_length = wave.sample_length
    data = wave.data_slice(begin_time, end_time)
    data = np.array(data)

    derivative = [0] * 2 # 
    for i in range(2,len(data)-2):
        derivative.append(
            (1/8) * (-data[i-2]-2*data[i-1]+2*data[i+1]+data[i+2]))
    derivative = derivative + [0] * 2
    derivative = np.array(derivative)

    window_width = 0.15/sample_length # 150 ms
    half_window = int(window_width/2) 
    integral = [0]  * half_window
    for i in range(half_window, len(derivative)-half_window):
        integral.append(np.sum(derivative[i-half_window:i+half_window]))
    integral = integral + [0] * half_window
    integral = np.array(integral)
    
    threshold = (
        np.max(integral[0:int(arguments['threshold_period']/sample_length)])
        * arguments['threshold_fraction'])
    dbp_x = []
    dbp_y = []
    begin_i = 0
    average_period = 0
    i = 0
    while i < len(integral):
        if integral[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(dbp_x)==0 or i*sample_length > dbp_x[-1] + arguments['safe_period'] - begin_time:
                    hopeful_slice = data[begin_i:i]
                    maximum_i = np.argmin(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    dbp_x.append(begin_time+sample_length*(fin_i-1))
                    dbp_y.append(data[fin_i])
                    threshold = np.max(integral[fin_i:fin_i+int(arguments['threshold_period']/sample_length)]) * arguments['threshold_fraction']
                    begin_i = 0
                    if len(dbp_x) > 3:
                        average_period = ( (dbp_x[-1]-dbp_x[-2]) + (dbp_x[-2]-dbp_x[-3]) + (dbp_x[-3]-dbp_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > dbp_x[-1] + average_period*1.7:
                threshold *= 0.6
                i = int((dbp_x[-1]+arguments['safe_period'])/sample_length)
        i += 1
    dbp_x = np.array(dbp_x)
    return dbp_x, dbp_y

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)
