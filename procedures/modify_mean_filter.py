from scipy.signal import butter, filtfilt
import numpy as np
from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """The procedure performs signal averaging
"""
author = 'mzylinski'
arguments = {
    'Sample count':"Number of sample use in average window"
}
default_arguments = {'Sample count':'100'}

def interpret_arguments(wave, points, arguments):
    "Sprawdza, czy podane argumenty są poprawne."
    #a
    try:
        a = int(arguments['Sample count'])
    except:
        raise InvalidArgumentError("Invalid filter order "
                                   "{}".format(arguments['Ilość próbek']))

    return {'Sample count':a}


def procedure(wave, begin_time, end_time, arguments):
    a = (arguments['Sample count'])
  
    data = wave.data_slice(begin_time, end_time)
    mean = 0
    for i in range(0,a):
        mean = mean + data[i]
        data[i] = mean / (i+1)
    for i in range((a),len(data)-(a)-1):
        data[i] = mean / a
        mean = mean + data[i+1]
        mean = mean - data[i+1-a]

    for i in range(len(data)-(a)-1, len(data)):
        data[i] = mean / (a)

    return data

def execute(wave, points,  begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points,  arguments)
    return procedure(wave, begin_time, end_time, arguments)
