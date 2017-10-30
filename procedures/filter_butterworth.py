from scipy.signal import butter, filtfilt
import numpy as np
procedure_type = 'filter'
description = """Procedura aplikująca filtr Butterwortha z biblioteki SciPy.
Wymagane argumenty:
['N']: int; rząd filtru
['Wn']: float; częstotliwość graniczna filtru w Hz. Jeśli ['btype'] wynosi 'bandpass' lub 'bandstop', ['Wn'] to numpy.array dwóch wartości.
Opcjonalne argumenty:
['btype']:'low': {‘lowpass’, ‘highpass’, ‘bandpass’, ‘bandstop’}; Typ filtra. 
Dokładna dokumentacja na https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.butter.html"""
author = 'kcybulski'
default_settings = {'N':None,'Wn':None,'btype':'low'}
required_arguments = ['N','Wn']
def procedure(data_line, begin_time, end_time, settings):
    if settings['N'] is None or settings['Wn'] is None:
            raise ValueError("Ustawienia N i Wn nie mogą być puste.")
    if isinstance(settings['Wn'],np.ndarray) and (settings['Wn'] > data_line.sample_rate/2).all() or not isinstance(settings['Wn'],np.ndarray) and settings['Wn'] > data_line.sample_rate/2: # data_line.sample_rate/2 to częstotliwość Nyquista, powyżej której funkcja nie działa
            raise ValueError("Opcja ['Wn'] jest zbyt duża. Maksymalnie może wynosić połowę częstotliwości danych.")
    wn = 2*settings['Wn']/data_line.sample_rate # funkcja butter(...) przyjmuje częstotliwość graniczną od 0 do 1, gdzie 1 to częstotliwość nyquista sygnału; tutaj zachodzi konwersja z hz na argument dla filtru
    b, a = butter(settings['N'],wn,btype=settings['btype'])
    data = data_line.data_slice(begin_time, end_time)
    return filtfilt(b,a,data)
