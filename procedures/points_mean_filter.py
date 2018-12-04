import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure step average points
""")
author = 'mzylinski'
arguments = {
     'N':"Number of sample to average"
    
    }
default_arguments = {
    'N':'15',
    }
output_type = 'mean'
required_waves = []
required_points = ['a']




def procedure(waves, points, begin_time, end_time, settings):
    a = points['a']

    N = int(settings['N'])
    n = 0
    i = 0

    sumMean = 0

    r_x = []
    r_y = []  
    
    while i < len(a.data_y):
        sumMean = sumMean + a.data_y[i]
        if (N == n):
            sumMean = sumMean - a.data_y[i-N]
        else:
            n = n + 1

        r_x.append(a.data_x[i])
        r_y.append(sumMean/n)
        i = i + 1
        


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