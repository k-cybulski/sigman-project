import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedure find maximum of the signal between R
""")
author = 'mzylinski'
arguments = {
     'Time after R [%]':"Define percent of cardiac cycle after R for detect maximum",
      'Blind spot [%]':"Percent of cardiac cycle which is omitted"
    }
default_arguments = {
    'Time after R [%]':100,
    'Blind spot [%]':0
    }
output_type = 'max'
required_waves = ['Signal']
required_points = ['R']



def procedure(waves, points, begin_time, end_time, settings):
    wave = waves['Signal']
    R = points['R']
    t = settings['Time after R [%]']/100
    blank = settings['Blind spot [%]']/100
    r_x = []
    r_y = []

    for i in range(0,len(R)-1):
        okres= (R.data_x[i+1]-R.data_x[i])
        data = wave.data_slice(R.data_x[i]+blank*okres, okres*t+R.data_x[i])
        if (len(data)>0):
            data_max = max(data);
            itemindex = np.where(data==data_max)[0]
            r_y.append(data_max)
            r_x.append(R.data_x[i] + itemindex[0]*wave.sample_length+blank*okres)


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