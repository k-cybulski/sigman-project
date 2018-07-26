import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure detect point B in ICG signal. Algorithm detect first minimum before dz/dtmax.
""")
author = 'mzylinski'
arguments = {
    }
default_arguments = {
    }
output_type = 'B'
required_waves = ['Signal']
required_points = [ 'R']


def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['Signal']
    R = points['R']
   

    r_x = []
    r_y = []

    for i in range(0,len(R)-1):
        data = wave.data_slice(R.data_x[i], R.data_x[i+1])
        data_max = max(data);
        
        itemindex = np.where(data==data_max)[0]
        while (data[itemindex[0]]*2)>=(data[itemindex[0]-1]+data[itemindex[0]-2]):
            itemindex[0] = itemindex[0]-1
            if itemindex[0]==2:
                break
        r_y.append(data[itemindex[0]])
        r_x.append(R.data_x[i] + itemindex[0]*wave.sample_length)


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