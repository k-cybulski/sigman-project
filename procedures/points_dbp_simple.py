from sigman import analyzer 
import numpy as np
procedure_type = 'points'
description = """Procedura aplikujący prosty algorytm do odnalezienia
punktów DBP na wykresie BP. Działa on w następujący sposób:
1) Oblicza pochodną wykresu BP
2) Przeprowadza całkowanie zakresowe (window integration) na pochodnej
3) Oblicza graniczną wartość (threshold) całki w oparciu o ułamek
    <threshold_fracion> najwyższej wartości całki w czasie
    <threshold_period> od początku / ostatniego wykrycia DBP
4) Na odcinkach na których wartość całki jest powyzej wartości
    granicznej znajduje najniższą wartość wykresu BP i oznacza go
    jako DBP. Czeka <safe_period> nim znowu możliwe będzie odnalezienie
    nowego DBP.
5) Jeśli przez ponad dwukrotnie dłuższy czas niż przewidywany nie 
    znalazł DBP, obniża wartość graniczną i cofa poszukiwanie do 
    ostatniego DBP.
"""
author = 'kcybulski'
default_settings = {'threshold_fraction':0.4,'threshold_period':2,'safe_period':0.25}
required_lines = ['bp']
required_points = []
required_arguments = []
def procedure(comp_data, begin_time, end_time, settings):
    data_line = comp_data.data_lines['bp']
    
    # Obliczamy pochodną za pomocą pięciu punktów (po 2 z każdej strony
    # punktu środkowego)
    sample_length = data_line.sample_length
    data = data_line.data_slice(begin_time, end_time)
    data = np.array(data)
    derivative = [0] * 2 # pierwsze dwie wartości są puste
    for i in range(2,len(data)-2):
        derivative.append( (1/8) * (-data[i-2]-2*data[i-1]+2*data[i+1]+data[i+2]) )
    derivative = derivative + [0] * 2 # dwie ostatnie wartości są puste
    derivative = np.array(derivative)

    # Przeprowadzamy całkowanie zakresowe (tłum. window integration) kwadratu pochodnej
    window_width = 0.15/sample_length # 150 ms
    half_window = int(window_width/2) 
    integral = [0]  * half_window 
    for i in range(half_window, len(derivative)-half_window):
        integral.append(np.sum(derivative[i-half_window:i+half_window]))
    integral = integral + [0] * half_window
    integral = np.array(integral)
    
    # Przejeżdżamy przez cały wykres i patrzymy gdzie całka pochodnej powyżej 
    # wartości granicznej. Tam, gdzie jest ona wyższa, odnajdujemy najniższą
    # wartość wykresu BP i stawiamy DBP.
    threshold = np.max(integral[0:int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
    dbp_x = []
    dbp_y = []
    thres = []
    begin_i = 0
    average_period = 0 # Tempo obliczamy po 3 biciach
    i = 0
    while i < len(integral):
        if integral[i] > threshold:
            if begin_i == 0:
                begin_i = i
        else:
            if begin_i != 0: 
                if len(dbp_x)==0 or i*sample_length > dbp_x[-1] + settings['safe_period'] - begin_time:
                    hopeful_slice = data[begin_i:i]
                    maximum_i = np.argmin(hopeful_slice)
                    fin_i = begin_i + maximum_i
                    dbp_x.append(begin_time+sample_length*(fin_i-1))
                    dbp_y.append(data[fin_i])
                    threshold = np.max(integral[fin_i:fin_i+int(settings['threshold_period']/sample_length)]) * settings['threshold_fraction']
                    begin_i = 0
                    if len(dbp_x) > 3:
                        average_period = ( (dbp_x[-1]-dbp_x[-2]) + (dbp_x[-2]-dbp_x[-3]) + (dbp_x[-3]-dbp_x[-4]) ) / 3
                    continue
                else:
                    begin_i = 0
            if average_period!=0 and i*sample_length > dbp_x[-1] + average_period*1.7:
                threshold *= 0.6
                i = int((dbp_x[-1]+settings['safe_period'])/sample_length)
        i += 1
    dbp_x = np.array(dbp_x)
#    from matplotlib import pyplot as plt
#    plt.plot(data)
#    plt.plot(derivative)
#    plt.plot(integral)
#    plt.plot(dbp_x/sample_length,dbp_y, marker='o', linestyle='None')
#    plt.show()
    return dbp_x, dbp_y
