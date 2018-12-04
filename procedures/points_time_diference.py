import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate difrence in time beatwin points:
    y = t1/t2
    y - result
    t1, t2 - time of points a and b
    result points time is taken as t1 (time of a points)
""")
author = 'mzylinski'
arguments = {
     
    
    }
default_arguments = {
    
    }
output_type = 'time_diff'
required_waves = []
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
        y = b.data_x[i]-a.data_x[i]

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