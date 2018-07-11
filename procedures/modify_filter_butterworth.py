from scipy.signal import butter, filtfilt
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """Procedure applying the Butterworth filter from SciPy.
Exact documentation here:
https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.butter.html"""
author = 'kcybulski'
arguments = {
    'N':"Order of the filter; natural number",
    'Wn':("Cutoff frequency in Hz. Wn may not be greater than the Nyquist "
          "frequency; real number or, if btype is bandpass or bandstop, two "
          "real numbers split with a comma."),
    'btype':"Type of filter; lowpass, highpass, bandpass or bandstop"
}
default_arguments = {'N':'','Wn':'','btype':'lowpass'}

def interpret_arguments(wave, points, arguments):
    # N
    try:
        N = int(arguments['N'])
        if N < 0:
            raise ValueError
    except:
        raise InvalidArgumentError("Invalid filter order "
                                   "{}".format(arguments['N']))
    # btype
    if (arguments['btype'] not in [
            'lowpass', 'highpass', 'bandpass', 'bandstop']):
        raise InvalidArgumentError("Invalid filter type "
                                   "{}".format(arguments['btype']))
    btype = arguments['btype']
    # Wn
    try:
        Wn = []
        if btype in ['bandpass', 'bandstop']:
            Wn_strings = arguments['Wn'].split(',')
            Wn = np.array([float(string) for string in Wn_strings])
        else:
            Wn = float(arguments['Wn'])
    except:
        raise InvalidArgumentError("Invalid cutoff frequency for this type"
                                   "{}".format(arguments['Wn']))
    if type(Wn) == float:
        _testvals = [Wn]
    else:
        _testvals = Wn
    if any(val > wave.sample_rate/2 for val in _testvals):
        raise InvalidArgumentError("Cutoff frequency may not be greater than "
                                   "half of waveform's sample rate.")
    return {
        'N':N,
        'Wn':Wn,
        'btype':btype}

def procedure(wave, begin_time, end_time, arguments):
    wn = 2*arguments['Wn'] / wave.sample_rate 
    b, a = butter(arguments['N'], wn, btype=arguments['btype'])
    data = wave.data_slice(begin_time, end_time)
    return filtfilt(b, a, data)

def execute(wave, points, begin_time, end_time, arguments):
    arguments = interpret_arguments(wave, points, arguments)
    return procedure(wave, points, begin_time, end_time, arguments)
