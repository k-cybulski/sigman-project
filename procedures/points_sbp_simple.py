from sigman import analyzer 
import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedura aplikująca prosty algorytm do odnalezienia punktów SBP 
na wykresie BP. Działa on w następujący sposób:
1) Normalizuje dane BP do zakresu <0;1>
2) Oblicza graniczną wartość (threshold) znormalizowanego BP w oparciu
    o ułamek <threshold_fraction> najwyższej wartości BP w czasie
    <threshold_period> od początku / od ostatniego wykrycia SBP
3) Na odcinkach na których wartość normalizowanego BP jest powyżej 
    wartości granicznej znajduje najwyższą wartość wykresu BP i oznacza
    go jako SBP. Czeka <safe_period> nim znowu możliwe będzie 
    odnalezienie nowego SBP.
""")
author = 'kcybulski'
arguments = {
    'threshold_fraction':("Wartość graniczna całki zakresowej, powyżej "
                          "której rozpatrywana jest możliwość istnienia "
                          "SBP."),
    'threshold_period':("Czas, na przestrzeni którego sprawdzane są "
                        "maksymalne wartości całki zakresowej."),
    'safe_period':"Czas, w którym nie można odnaleźć dwóch SBP obok siebie."}
default_arguments = {
    'threshold_fraction':0.6,
    'threshold_period':2,
    'safe_period':0.25}
required_waves = ['bp']
required_points = []

def validate_arguments(composite_data, arguments):
    """Sprawdza, czy podane argumenty są poprawne."""
    # Wszystkie powinny być zwykłymi floatami
    for key, item in arguments.items():
        try:
            float(item)
        except:
            error_message = key + " niewłaściwy"
            return False, error_message
    return True, ""

def interpret_arguments(arguments):
    """Konwertuje argumenty tekstowe w liczby."""
    output_arguments = {}
    for key, item in arguments.items():
        output_arguments[key] = float(item)
    return output_arguments

def procedure(comp_data, begin_time, end_time, settings):
    data_wave = comp_data.data_waves['bp']
    
    sample_length = data_wave.sample_length
    data = data_wave.data_slice(begin_time, end_time)
    data = np.array(data)

    # Normalizujemy dane do zakresu <0,1> by ułatwić odnajdywanie wartości granicznej
    normalized_data = data - np.min(data)
    normalized_data /= np.max(normalized_data)

    threshold = np.max(normalized_data[0:int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
    sbp_x = []
    sbp_y = []
    begin_i = 0
    average_period = 0 # Tempo obliczamy po 3 biciach
    i = 0
    while i < len(data):
        if normalized_data[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(sbp_x)==0 or i*sample_length > sbp_x[-1] + settings['safe_period'] - begin_time:
                    hopeful_slice = normalized_data[begin_i:i]
                    maximum_i = np.argmax(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    sbp_x.append(begin_time+sample_length*(fin_i-1))
                    sbp_y.append(data[fin_i])
                    threshold = np.max(normalized_data[fin_i:fin_i+int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
                    begin_i = 0
                    if len(sbp_x) > 3:
                        average_period = ( (sbp_x[-1]-sbp_x[-2]) + (sbp_x[-2]-sbp_x[-3]) + (sbp_x[-3]-sbp_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > sbp_x[-1] + average_period*2:
                threshold *= 0.6
                i = int((sbp_x[-1]+settings['safe_period'])/sample_length)
        i += 1
    sbp_x = np.array(sbp_x)
    return sbp_x, sbp_y

def execute(comp_data, begin_time, end_time, arguments):
    """Sprawdza poprawność argumentów i wykonuje procedurę."""
    valid, error_message = validate_arguments(comp_data, arguments)
    if not valid:
        raise InvalidArgumentError(error_message)
    arguments = interpret_arguments(arguments)
    return procedure(comp_data, begin_time, end_time, arguments)
