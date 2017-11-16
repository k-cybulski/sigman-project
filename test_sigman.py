#!/usr/bin/env python3
# Ten skrypt sprawdza działanie wszystkich funkcji pakietu sigman

import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis
import os

os.path.dirname(os.path.abspath(__file__))

print(">Próba importu próbych .dat")
bp_wave = fm.import_wave('example_data/BP.dat', wave_type = 'bp')
ecg_wave = fm.import_wave('example_data/EKG.dat', wave_type = 'ecg')
r_points = fm.import_points('example_data/R.dat', point_type = 'r') 

print(">Próba połączenia danych w Composite_data")
waves={'bp':bp_wave, 'ecg':ecg_wave}
points={'r':r_points}
complete_data = sm.Composite_data(waves = waves, points = points)

print(">Próba wizualizacji danych w całości")
vis.visualize_composite_data(complete_data, title="Całość")

print(">Próba wizualizacji wycinka danych")
vis.visualize_composite_data(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy")

print(">Próba wizualizacji wycinka z jednym przebiegiem offsetowanym")
complete_data.waves['bp'].offset = -0.2
vis.visualize_composite_data(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy z offsetem -0.2s na BP")
complete_data.waves['bp'].offset = 0


print(">Próba importu procedury filtrowania")
module = analyzer.import_procedure("filter_butterworth")
print("Procedure type:",module.procedure_type)
print("Description:",module.description)
print("Author:",module.author)

print(">Próba przefiltrowania danych zewnętrzną procedurą filtrowania")
butterworth = analyzer.import_procedure("filter_butterworth")
arguments = butterworth.default_arguments
arguments['N'] = 3
arguments['Wn'] = 30
filtered_wave = analyzer.filter_wave(complete_data.waves['bp'], 60, 70, butterworth, arguments)
complete_data.waves['bp'].replace_slice(60, 70, filtered_wave)
vis.visualize_composite_data(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy po filtracji 30 Hz na zakresie <60s;70s>")

print(">Próba usunięcia zakresu punktów")
complete_data.points['r'].delete_slice(65,75)
vis.visualize_composite_data(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy po usunięciu punktów")

print(">Próba zapisania composite_data")
fm.save_composite_data("example_data/example_composite_data.pickle",complete_data)

print(">Proba wczytania innego, bardzo chaotycznego sygnału EKG i przefiltrowania go a następnie pokazania tuż obok nieprzefiltrowanego")
ecg_wave = fm.import_wave('example_data/EKG_messy.dat', wave_type = 'ecg_messy')
arguments['N'] = 3
arguments['Wn'] = 20
filtered_ecg = analyzer.filter_wave(ecg_wave, 0, ecg_wave.complete_length, butterworth, arguments)
complete_data = sm.Composite_data(waves={'ecg_messy':ecg_wave,'ecg':filtered_ecg})
vis.visualize_composite_data(complete_data, begin_time=10,end_time=15,title="EKG wejściowe (mocno zaburzone) oraz przefiltrowane filtrem 20 Hz")

print(">Próba ponownego wczytania wcześniej zapisanego composite_data")
complete_data = fm.load_composite_data('example_data/example_composite_data.pickle')
vis.visualize_composite_data(complete_data, title="Wczytany ponownie")
os.remove('example_data/example_composite_data.pickle')

#TODO: Odnajdywanie punktów na wykresie
print(">Próba odnalezienia r na odcinku <65s, 75s>")
find_r = analyzer.import_procedure('points_r_simple')
arguments = find_r.default_arguments
found_points = analyzer.find_points(complete_data, 65, 75, find_r, arguments, point_type = 'r')
complete_data.add_points(found_points, 'r', join=True)
vis.visualize_composite_data(complete_data, begin_time = 60, end_time = 80, title = "Dane z odnalezionymi ponownie R-ami")

print(">Próba usunięcia i odnalezienia wszystkich r")
complete_data.delete_points('r')
begin_time, end_time = complete_data.calculate_time_range(required_waves=['ecg'])
found_points = analyzer.find_points(complete_data, begin_time, end_time, find_r, arguments, point_type = 'r')
complete_data.add_points(found_points, 'r')
vis.visualize_composite_data(complete_data, title = "Dane z całkowicie nowymi R-ami")

print(">Próba obliczenia tempa bicia serca na kilku interwałach")
calculate_hr = analyzer.import_procedure('parameter_heart_rate')
param_tuples = []
for i in range(10,100,10):
    param_tuples.append((i-10,i))
hr = analyzer.calculate_parameter(complete_data, param_tuples ,calculate_hr,
                                  calculate_hr.default_arguments, 'hr')
complete_data.add_parameter(hr, 'hr')
vis.visualize_composite_data(complete_data, begin_time = 0, end_time = 120,
                             title = "Wycinek <0s; 120s> z parametrem")


print(">Próba usunięcia pojedynczego punktu r i zastąpienia go nowym")
vis.visualize_composite_data(complete_data, begin_time = 240, end_time = 243, title = "Wycinek <240s; 243s>")
complete_data.points['r'].delete_point(241) #,y=5.8)
x = 241.227
y = complete_data.waves['ecg'].value_at(x)
complete_data.points['r'].add_point(x,y)
vis.visualize_composite_data(complete_data, begin_time = 240, end_time = 243, title = "Wycinek <240s; 243s> z zamienionym punktem na 241s")

print(">Próba oznaczenia SBP i DBP")
find_sbp = analyzer.import_procedure('points_sbp_simple')
arguments = find_sbp.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['bp'])
found_sbp = analyzer.find_points(complete_data, begin_time, end_time, find_sbp, arguments, point_type = 'sbp')
complete_data.add_points(found_sbp, 'sbp')
find_dbp = analyzer.import_procedure('points_dbp_simple')
arguments = find_dbp.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['bp'])
found_dbp = analyzer.find_points(complete_data, begin_time, end_time, find_dbp, arguments, point_type = 'dbp')
complete_data.add_points(found_dbp, 'dbp')
vis.visualize_composite_data(complete_data, title="Dane z odnalezionymi SBP i DBP")

print(">Próba oznaczenia DN")
find_dn = analyzer.import_procedure('points_dn_net')
arguments = find_dn.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['ecg','bp'])
found_dn = analyzer.find_points(complete_data, begin_time, end_time, find_dn, arguments, point_type = 'dn')
complete_data.add_points(found_dn, 'dn')
vis.visualize_composite_data(complete_data, title="Dane z odnalezionymi DN")
