import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure detect X point in ICG as the first minimum of the signal after dz/dt points.
""")
author = 'mzylinski'
arguments = {
    'Time limit [%]':("Limiting the time of the heart cycle in which the minimum is sought"),
    'Sample count':("Argument define number of sumple use to detect minimum.")
    }
default_arguments = {
    'Time limit [%]':70,
    'Sample count':2
    }
output_type = 'X'
required_waves = ['Signal']
required_points = ['points']


def procedure(waves, points, begin_time, end_time, settings):
 

    wave = waves['Signal']
    R = points['points']
    t = settings['Time limit [%]']/100
    IP = int(settings['Sample count'])
    r_x = []
    r_y = []

    for i in range(0,len(R)-1):
        data = wave.data_slice(R.data_x[i], R.data_x[i]+(R.data_x[i+1]-R.data_x[i])*t)

        
        itemindex = len(data)-IP-1
        if (itemindex>0):
            #Upewniam się że jestem na zboczu opadajacym
            while (data[itemindex]<data[itemindex-1]):
                itemindex = itemindex - 1
                if itemindex==IP:
                    break
            #a nastepnie szukam minimum
            while not ((data[itemindex+IP]>data[itemindex]) and (data[(itemindex-IP)]>data[itemindex])):
                itemindex = itemindex-1
                if itemindex==IP:
                    break
        else:
            itemindex = 0;
        r_y.append(data[itemindex])
        r_x.append(R.data_x[i] + itemindex*wave.sample_length)


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