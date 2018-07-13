from scipy.signal import butter, filtfilt
import numpy as np
import statistics
from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """The procedure performs median signal filtration
"""
author = 'mzylinski'
arguments = {
    'Sample count':"Number of sample use to median operation (1 + Sample count *2)"
}
default_arguments = {'Sample count':'1'}


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
    for i in range((a),len(data)-(a)):
        items = data[range (i-a,i+a+1)]
        data[i] = statistics.median(items)
    return data

def execute(wave, points,  begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points,  arguments)
    return procedure(wave, begin_time, end_time, arguments)