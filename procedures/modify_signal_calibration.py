from scipy.signal import butter, filtfilt
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """Procedure perform linear calibration of the signal:
        y1 = a*y + b
"""
author = 'mzylinski'
arguments = {
    'a':"calibration factor",
    'b':"offset"
}
default_arguments = {'a':'1','b':'0'}


def interpret_arguments(wave, points, arguments):
    "Sprawdza, czy podane argumenty są poprawne."
    #a
    try:
        a = float(arguments['a'])
    except:
        InvalidArgumentError("Invalid filter order "
                                   "{}".format(arguments['a']))
    #b
    try:
        b = float(arguments['b'])
    except:
        raise InvalidArgumentError("Invalid filter order "
                                   "{}".format(arguments['b']))

    return {'a':a,
            'b':b}

def procedure(wave, begin_time, end_time, arguments):
    a = arguments['a']
    b = arguments['b']
    
    data = wave.data_slice(begin_time, end_time)
    for i in range(0,len(data)):
        data[i] = a*data[i]+b
    return data

def execute(wave, points,  begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points,  arguments)
    return procedure(wave, begin_time, end_time, arguments)
