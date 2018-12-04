import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure calculate stroke volume (SV) as area of pressure under systele subtract 
area from filling:
 Wang-NiewiadomskiArea = (P(end_systole)-P(start_systole)*ET)/2
 
""")
author = 'mzylinski'
arguments = {
         }
default_arguments = {
       }
output_type = 'SV'
required_waves = ['AP']
required_points = ['DBP',  'ET']

def calculateArea (pressure,dt):
    area = 0
    for i in range(0,len(pressure)-1):
        dp = ((pressure[i]+pressure[i+1])*dt) / 2
        area = area + dp 

    return area

def procedure(waves, points, begin_time, end_time, settings):
    DBP = points['DBP']
    ET = points['ET']
    AP = waves['AP']
    
    ET_X,ET_Y = ET.data_slice (begin_time,end_time)
    DBP_X,DBP_Y = DBP.data_slice (begin_time,end_time)

    dt = 1 / AP.sample_rate
    r_x = []
    r_y = []

    if (len(DBP_X)<len(ET_Y)):
        N = len(DBP_X)
    else:
        N = len(ET_Y)

    for i in range(0,N):
            pressure = AP.data_slice(DBP.data_x[i], DBP.data_x[i]+ET_Y[i])
            areaSystole = calculateArea(pressure,dt)
            
            WNArea = (pressure[0]+pressure[-1])*ET_Y[i]/2

            SV = areaSystole - WNArea
            r_x.append(DBP.data_x[i])

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