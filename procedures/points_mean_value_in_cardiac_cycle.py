
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = ("""Procedure calculate mean value of the signal in cardiac cycles
""")
author = 'mzylinski'
arguments = {
    }
default_arguments = {
    }
output_type = 'mean'
required_waves = ['Signal']
required_points = ['R']



def mean(data):
    sum = 0
    if (len(data)> 0):
        for i in range(0,len(data)):
            sum = sum + data[i]

        return sum / len(data)
    else:
        return 0

def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['Signal']
    R = points['R']

    r_x = []
    r_y = []

    for i in range(0,len(R) - 1):
        if (R.data_x[i]>begin_time and R.data_x[i + 1] < end_time):
            data = wave.data_slice(R.data_x[i], R.data_x[i + 1])
                
            r_y.append(mean(data))
            r_x.append(R.data_x[i])

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