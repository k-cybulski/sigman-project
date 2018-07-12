import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate stroke volume (SV) base on Kubicek's formula:
 SV = p*L0*Z0^-2*dz/dtmax*ET
 where:
    p - blood resistivity [Ohm*cm]
    L0 - length of the segment [cm]
    Z0 - value of the Z0 
    dz/dt max - maximum value of the ICG dz/dt signal
    ET - ejection time (time between points B and X)
""")
author = 'mzylinski'
arguments = {
     'L0':("length of the segment [cm]"),
     'p':("blood resistivity [Ohm*cm]")
    }
default_arguments = {
    'L0':20,
    'p':135
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
    p = settings['p']
    L0 = settings['L0']
    for i in range(0,len(B)-1):
        ET =  X.data_x[i] - B.data_x[i]
        
        SV = p*L0*L0*dZdtmax.data_y[i]*ET/(z0.data_y[i]*z0.data_y[i])
       
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