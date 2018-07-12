import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure detect X point in ICG as the signal minimum after dz/dt points.
""")
author = 'mzylinski'
arguments = {
    'Time':("Limiting the time of the heart cycle in which the minimum is sought")
    }
default_arguments = {
    'Time':0.7,
    }
output_type = 'X'
required_waves = ['Signal']
required_points = ['dzmax']


def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['Signal']
    dzmax = points['dzmax']
 

    r_x = []
    r_y = []

    for i in range(0,len(dzmax)-1):
        if (dzmax.data_x[i+1]<(wave.complete_length+wave.offset))and (dzmax.data_x[i]>wave.offset):
            data = wave.data_slice(dzmax.data_x[i], dzmax.data_x[i]+(dzmax.data_x[i+1]-dzmax.data_x[i])*settings['Time'])
            data_max = min(data);
        
            itemindex = np.where(data==data_max)[0]
    
            r_y.append(data[itemindex[0]])
            r_x.append(dzmax.data_x[i] + itemindex[0]*wave.sample_length)


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