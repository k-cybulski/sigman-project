import numpy as np
import math
from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate stroke volume (SV) base on Sramek's formula:
 SV = ((0,17*Height)^3/4,2)*(dz/dtmax)*ET/Z0
 where:
    Z0 - value of the Z0 
    dz/dt max - maximum value of the ICG dz/dt signal
    ET - ejection time (time between points B and X)
""")
author = 'mzylinski'
arguments = {
     'height':'1.75'
    }
default_arguments = {
    'height':175
    }
output_type = 'SV'
required_waves = []
required_points = ['dZ/dtmax',  'Z0', 'B_ICG','X_ICG']



def procedure(waves, points, begin_time, end_time, settings):
    dZdtmax = points['dZ/dtmax']
    z0 = points['Z0']
    B = points['B_ICG']
    X = points['X_ICG']

    r_x = []
    r_y = []

    height = float(settings['height'])
    dim_cor = math.pow (0.17*height,3)/4.2
    for i in range(0,len(B)-1):
        ET =  X.data_x[i] - B.data_x[i]
        
        SV = dim_cor*dZdtmax.data_y[i]*ET/(z0.data_y[i])
       
        r_x.append(dZdtmax.data_x[i])
        r_y.append(SV)


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