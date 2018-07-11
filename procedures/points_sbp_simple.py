from sigman import analyzer 
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""
Procedure applying a simple algorithm to find SBP points on a BP
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
    'safe_period':"Period in which two SBPs cannot be found."}
default_arguments = {
    'threshold_fraction':0.6,
    'threshold_period':2,
    'safe_period':0.25}
output_type = 'sbp'
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

def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['bp']
    
    sample_length = wave.sample_length
    data = wave.data_slice(begin_time, end_time)
    data = np.array(data)

    normalized_data = data - np.min(data)
    normalized_data /= np.max(normalized_data)

    threshold = np.max(normalized_data[0:int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
    sbp_x = []
    sbp_y = []
    begin_i = 0
    average_period = 0
    i = 0
    while i < len(data):
        if normalized_data[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(sbp_x)==0 or i*sample_length > sbp_x[-1] + settings['safe_period'] - begin_time:
                    hopeful_slice = normalized_data[begin_i:i]
                    maximum_i = np.argmax(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    sbp_x.append(begin_time+sample_length*(fin_i-1))
                    sbp_y.append(data[fin_i])
                    threshold = np.max(normalized_data[fin_i:fin_i+int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
                    begin_i = 0
                    if len(sbp_x) > 3:
                        average_period = ( (sbp_x[-1]-sbp_x[-2]) + (sbp_x[-2]-sbp_x[-3]) + (sbp_x[-3]-sbp_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > sbp_x[-1] + average_period*2:
                threshold *= 0.6
                i = int((sbp_x[-1]+settings['safe_period'])/sample_length)
        i += 1
    sbp_x = np.array(sbp_x)
    return sbp_x, sbp_y

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)
