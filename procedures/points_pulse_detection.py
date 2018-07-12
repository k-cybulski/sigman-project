import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure perform pulse detection (eq. markers, handgrip etc.). Procedure has two methods of pulse detection: base on given treshold or base on mean value of the signal.
""")
author = 'mzylinski'

output_type = 't'
required_waves = ['Signal']
required_points = []
arguments = {
     'multiply mean':("Pulse detected when signal exeed mean value multiply by this value. 0 - disable this method"),
     'treshold':("Pulses are detected when the signal will exeed the treshold"),
     'Begin or end':("1 - mark only beginning of the pulse;"
     "2 - mark end of the pulse;" 
     "3 - mark beginning and end of the pulse")
    }
default_arguments = {
    'multiply mean':0,
    'treshold':0,
    'Begin or end':1
    }


def mean(data):
    sum = 0
    for i in range(0,len(data)):
        sum = sum + data[i]

    return sum / len(data)

def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['Signal']
 

    r_x = []
    r_y = []
    
    data = wave.data_slice(begin_time, end_time)
    if (settings['multiply mean']!= 0):
        prog = mean(data)*settings['multiply mean']
    else:
        prog = settings['treshold']

    flag = 0;
    for i in range(0,len(data)):
        if (flag == 0):
            if (data[i]>prog):
                flag = 1
                if ((settings['Begin or end']%2) == 1):
                    r_y.append(data[i])
                    r_x.append(i*wave.sample_length)
        else:
            if (data[i]<prog):
                flag = 0;
                if (settings['Begin or end']>1):
                    r_y.append(data[i])
                    r_x.append(i*wave.sample_length)


    return r_x, r_y

def interpret_arguments(waves, points, arguments):
    output_arguments = {}
    for key, item in arguments.items():
        try:
            output_arguments[key] = float(item)
        except:
            raise InvalidArgumentError("{} is invalid.".format(arguments[key]))
    return output_arguments

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)