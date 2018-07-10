from scipy.signal import butter, filtfilt
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'modify'
description = """Procedura aplikująca filtr Butterwortha z biblioteki SciPy.
Dokładna dokumentacja na
https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.butter.html"""
author = 'kcybulski'
arguments = {
    'N':"Rząd filtru; liczba naturalna",
    'Wn':("Częstotliwość graniczna w Hz. Żadna wartość Wn nie może przekroczyć "
    "częstotliwości Nyquista (połowy częstotliwości samplowania przebiegu); "
    "liczba rzeczywista lub, jeśli btype wynosi bandpass lub bandstop, dwie "
    "liczby rzeczywiste przedzielone przecinkiem"),
    'btype':"""Typ filtru.
    lowpass - dolnoprzepustowy
    highpass - górnoprzepustowy
    bandpass - środkowoprzepustowy
    bandstop - środkowozaporowy"""
}
default_arguments = {'N':'','Wn':'','btype':'lowpass'}

def validate_arguments(wave, arguments):
    "Sprawdza, czy podane argumenty są poprawne."
    # btype
    if (arguments['btype'] not in [
            'lowpass', 'highpass', 'bandpass', 'bandstop']):
        return False, "Niewłaściwy typ filtru."
    # N
    try:
        value = int(arguments['N'])
        if value < 0:
            return False, "Za mały rząd filtru."
    except:
        return False, "Niewłaściwy rząd filtru."
    # Wn
    if arguments['btype'] in ['bandpass', 'bandstop']:
        try:
            vals = arguments['Wn'].split(',')
            if len(vals) != 2:
                return False, ("Niewłaściwa liczba częstotliwości "
                               "granicznych.")
            for val in vals:
                value = float(val)
                if value > wave.sample_rate/2:
                    return False, ("Zbyt duża częśtotliwość graniczna. "
                        "Maksymalnie może wynosić połowę częstotliwości "
                        "przebiegu.")
                if value < 0:
                    return False, "Zbyt mała częstotliwość graniczna."
        except:
            return False, "Niewłaściwe częstotliwości graniczne."
    else:
        try:
            value = float(arguments['Wn'])
            if value > wave.sample_rate/2:
                return False, ("Zbyt duża częśtotliwość graniczna. "
                     "Maksymalnie może wynosić połowę częstotliwości "
                     "przebiegu.")
            if value < 0:
                return False, "Zbyt mała częstotliwość graniczna."
        except:
            return False, "Niewłaściwa częstotliwość graniczna."
    return True, ""

def interpret_arguments(arguments):
    "Konwertuje argumenty tekstowe w liczby/inne wymagane typy."
    N = int(arguments['N'])
    btype = arguments['btype']
    Wn = []
    if btype in ['bandpass', 'bandstop']:
        Wn_strings = arguments['Wn'].split(',')
        for string in Wn_strings:
            Wn.append(float(string))
        Wn = np.array(Wn)
    else:
        Wn = float(arguments['Wn'])
    return {
        'N':N,
        'Wn':Wn,
        'btype':btype}

def procedure(wave, begin_time, end_time, arguments):
    wn = 2*arguments['Wn'] / wave.sample_rate # funkcja butter(...) przyjmuje częstotliwość graniczną od 0 do 1, gdzie 1 to częstotliwość nyquista sygnału; tutaj zachodzi konwersja z hz na argument dla filtru
    b, a = butter(arguments['N'], wn, btype=arguments['btype'])
    data = wave.data_slice(begin_time, end_time)
    return filtfilt(b, a, data)

def execute(wave,  points,begin_time, end_time, arguments):
    "Sprawdza poprawność argumentów i wykonuje procedurę."
    valid, error_message = validate_arguments(wave, arguments)
    if not valid:
        raise InvalidArgumentError(error_message)
    arguments = interpret_arguments(arguments)
    return procedure(wave, begin_time, end_time, arguments)
