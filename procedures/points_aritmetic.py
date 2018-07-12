import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure perform basic math operation on given pare of the points (+-*/), as example:
   y[t] = a[t]+b[t]
   Time is taken from a.
""")
author = 'mzylinski'
arguments = {
     'Operation':("+ - addition;"
     "- - subtraction;" 
     "* - multiplication;"
     "/ - division;"
     "sqr - roots a")
    }
default_arguments = {
    'Operation':'+',
    }
output_type = 'Points'
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
        if (settings['operacja']== '+'):
            y = a.data_y[i]+b.data_y[i]
        if (settings['operacja']== '-'):
            y = a.data_y[i]-b.data_y[i]
        if (settings['operacja']== '*'):
            y = a.data_y[i]*b.data_y[i]
        if (settings['operacja']== 'sqr'):
            y = np.sqrt(a.data_y[i])
        if (settings['operacja']== '/'):
            if (b.data_y[i] != 0):
                y = a.data_y[i]/b.data_y[i]
            else:
                y = 0
        r_x.append(a.data_x[i])
        r_y.append(y)


    return r_x, r_y



def interpret_arguments(waves, points, arguments):
    output_arguments = {}
    for key, item in arguments.items():
        if (item != '+' and item != '-' and item != '*'and item != 'sqr' and item != '/'):
             raise InvalidArgumentError("{} is invalid.".format(arguments[key]))
        else:
             output_arguments[key] = item
    return output_arguments

def execute(waves, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(waves, points, arguments)
    return procedure(waves, points, begin_time, end_time, arguments)