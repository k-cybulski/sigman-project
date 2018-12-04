from scipy.signal import butter, filtfilt
import numpy as np
from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """Return the gradient of wave.

The gradient is computed using second order accurate central 
differences in the interior points and either first or second
order accurate one-sides (forward or backwards) differences 
at the boundaries. The returned gradient hence has 
the same shape as the input array.
"""
author = 'mzylinski'
arguments = {
    'Sample count':"Spacing between f values."
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
   

    return np.gradient(data, a)

def execute(wave, points,  begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points,  arguments)
    return procedure(wave, begin_time, end_time, arguments)
