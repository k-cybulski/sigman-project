import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate pulse wave velocity PWV as:
    PWV = L/t
    L - distance between sensors - path of the pulse wave
    t - time between points t[i] = b[i].data_x - a[i].data_x
""")
author = 'mzylinski'
arguments = {
     'distance':"distance between sensors - path of the pulse wave"
    
    }
default_arguments = {
    'distance':'0.15',
    }
output_type = 'PWV'
required_waves = ['']
required_points = ['a',  'b']




def procedure(waves, points, begin_time, end_time, settings):
    a = points['a']
    b = points['b']
    

    r_x = []
    r_y = []
  
    if (len(a)>= len(b)):
        d = len (b)-1
    else:
        d = len (a)-1

    for i in range(0,d):
        T = b.data_x[i]-a.data_x[i]
        if (T!= 0):
            y = float(settings['distance'])/T
        else:
            y = 0
        r_x.append(a.data_x[i])
        r_y.append(y)


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