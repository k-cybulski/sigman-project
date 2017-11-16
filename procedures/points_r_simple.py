import numpy as np

from sigman.analyzer import InvalidArgumentError

procedure_type = 'points'
description = (
"""Procedura aplikująca prosty algorytm do odnalezienia punktów R
na wykresie EKG. Działa on w następujący sposób:
1) Oblicza kwadrat pochodnej wykresu EKG
2) Przeprowadza całkowanie zakresowe (window integration) na kwadracie
    pochodnej
3) Oblicza graniczną wartość (threshold) całki w oparciu o ułamek
    <threshold_fraction> najwyższej wartości całki w czasie
    <threshold_period> od początku / od ostatniego wykrycia R
4) Na odcinkach na których wartość całki jest powyżej wartości
    granicznej znajduje najwyższą wartość wykresu EKG i oznacza go
    jako R. Czeka <safe_period> nim znowu możliwe będzie odnalezienie
    nowego R.
""")
author = 'kcybulski'
arguments = {
    'threshold_fraction':("Wartość graniczna całki zakresowej, powyżej "
                          "której rozpatrywana jest możliwość istnienia "
                          "R."),
    'threshold_period':("Czas, na przestrzeni którego sprawdzane są "
                        "maksymalne wartości całki zakresowej."),
    'safe_period':"Czas, w którym nie można odnaleźć dwóch R obok siebie."}
default_arguments = {
    'threshold_fraction':0.7,
    'threshold_period':2,
    'safe_period':0.25}
required_waves = ['ecg']
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
    wave = comp_data.waves['ecg']
    
    # Obliczamy kwadrat pochodnej
    sample_length = wave.sample_length
    data = wave.data_slice(begin_time, end_time)
    data = np.array(data)
    # pierwsze dwie wartości puste dla konsystencji czasowej z data
    derivative = [0] * 2
    for i in range(2,len(data)-2):
        derivative.append(( (1/8) * (-data[i-2]-2*data[i-1]+2*data[i+1]+data[i+2]) )**2) # wzór z oryginału
    derivative = derivative + [0] * 2 # dla konsystencji
    derivative = np.array(derivative)

    # Przeprowadzamy całkowanie zakresowe (tłum. window integration) kwadratu pochodnej
    window_width = 0.15/sample_length # 150 ms
    half_window = int(window_width/2) 
    integral = [0]  * half_window 
    for i in range(half_window, len(derivative)-half_window):
        integral.append(np.sum(derivative[i-half_window:i+half_window]))
    integral = integral + [0] * half_window
    integral = np.array(integral)
    
    # Przejeżdżamy przez cały wykres i patrzymy gdzie całka kwadratu pochodnej jest powyżej wartości granicznej
    # Tam, gdzie jest ona wyższa, odnajdujemy najwyższą wartość wykresu EKG i stawiamy tam R
    threshold = np.max(integral[0:int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
    r_x = []
    r_y = []
    begin_i = 0
    average_period = 0 # Tempo obliczamy po 3 biciach
    i = 0
    while i < len(integral):
        if integral[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(r_x)==0 or i*sample_length > r_x[-1] + settings['safe_period'] - begin_time:
                    hopeful_slice = data[begin_i:i]
                    maximum_i = np.argmax(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    r_x.append(begin_time+sample_length*(fin_i-1))
                    r_y.append(data[fin_i])
                    threshold = np.max(integral[fin_i:fin_i+int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
                    begin_i = 0
                    if len(r_x) > 3:
                        average_period = ( (r_x[-1]-r_x[-2]) + (r_x[-2]-r_x[-3]) + (r_x[-3]-r_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > r_x[-1] + average_period*1.7:
                threshold *= 0.6
                i = int((r_x[-1]+settings['safe_period'])/sample_length)
        i += 1
    r_x = np.array(r_x)
    return r_x, r_y

def execute(comp_data, begin_time, end_time, arguments):
    """Sprawdza poprawność argumentów i wykonuje procedurę."""
    valid, error_message = validate_arguments(comp_data, arguments)
    if not valid:
        raise InvalidArgumentError(error_message)
    arguments = interpret_arguments(arguments)
    return procedure(comp_data, begin_time, end_time, arguments)
