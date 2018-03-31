#!/usr/bin/env python3
# W tym skrypcie zademonstrowane są wszystkie główne metody biblioteki sigman

import sys
import os
_script_path = os.path.abspath(__file__)
_script_directory = os.path.dirname(_script_path)
_sigman_root_directory = os.path.dirname(_script_directory)
os.chdir(_script_directory)
sys.path.append(_sigman_root_directory)

import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer
from sigman import visualizer as vis

print(">Próba importu próbych .dat")
bp_wave = fm.import_wave('example_data/BP.dat', 'bp')
ecg_wave = fm.import_wave('example_data/EKG.dat', 'ecg')
r_points = fm.import_points('example_data/R.dat', 'r') 

print(">Próba połączenia danych w Composite_data")
waves={'bp':bp_wave, 'ecg':ecg_wave}
points={'r':r_points}
complete_data = sm.Composite_data(waves=waves, points=points)

print(">Próba wizualizacji danych w całości")
vis.show(complete_data, title="Całość")

print(">Próba wizualizacji wycinka danych")
vis.show(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy")

print(">Próba wizualizacji wycinka z jednym przebiegiem przesuniętym w czasie")
complete_data.waves['bp'].offset = -0.2
vis.show(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy z offsetem -0.2s na BP")
complete_data.waves['bp'].offset = 0

print(">Próba importu zewnętrznej procedury filtrowania i przefiltrowania nią danych")
butterworth = analyzer.import_procedure("modify_filter_butterworth")
print("Procedure type:",butterworth.procedure_type)
print("Description:",butterworth.description)
print("Author:",butterworth.author)

arguments = butterworth.default_arguments
arguments['N'] = 3
arguments['Wn'] = 30
modified_wave = analyzer.modify_wave(complete_data.waves['bp'], 60, 70, butterworth, arguments)
complete_data.waves['bp'].replace_slice(60, 70, modified_wave)
vis.show(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy po filtracji 30 Hz na zakresie <60s;70s>")

print(">Próba usunięcia punktów na danym zakresie")
complete_data.points['r'].delete_slice(65,75)
vis.show(complete_data, begin_time=60, end_time=80, title="Wycinek dwudziestosekundowy po usunięciu punktów")

print(">Próba zapisania composite_data")
fm.save_composite_data("example_data/example_composite_data.pickle",complete_data)

print(">Proba wczytania innego, bardzo chaotycznego sygnału EKG i przefiltrowania go a następnie pokazania tuż obok nieprzefiltrowanego")
ecg_wave = fm.import_wave('example_data/EKG_messy.dat', 'ecg')
arguments['N'] = 3
arguments['Wn'] = 20
modified_ecg = analyzer.modify_wave(ecg_wave, 0, ecg_wave.complete_length,
                                    butterworth, arguments)
complete_data = sm.Composite_data(waves={'ecg_messy':ecg_wave,'ecg_clean':modified_ecg})
vis.show(complete_data, begin_time=10,end_time=15,title="EKG wejściowe (mocno zaburzone) oraz przefiltrowane filtrem 20 Hz")

print(">Próba ponownego wczytania wcześniej zapisanego composite_data")
complete_data = fm.load_composite_data('example_data/example_composite_data.pickle')
vis.show(complete_data, title="Wczytany ponownie composite_data")
os.remove('example_data/example_composite_data.pickle')

print(">Próba odnalezienia r na odcinku <65s, 75s>")
find_r = analyzer.import_procedure('points_r_simple')
arguments = find_r.default_arguments
found_points = analyzer.find_points(complete_data.waves, complete_data.points, 65, 75, find_r, arguments)
complete_data.add_points(found_points, 'r', join=True)
vis.show(complete_data, begin_time=60, end_time=80,
                             title="Dane z odnalezionymi ponownie na zakresie <65s, 75s> R-ami")

print(">Próba usunięcia i odnalezienia wszystkich r")
complete_data.delete_points('r')
begin_time, end_time = complete_data.calculate_time_range(required_waves=['ecg'])
found_points = analyzer.find_points(complete_data.waves, complete_data.points, begin_time, end_time, find_r, arguments)
complete_data.add_points(found_points, 'r')
vis.show(complete_data, title="Dane z całkowicie nowymi R-ami")

print(">Próba obliczenia tempa bicia serca na kilku interwałach")
calculate_hr = analyzer.import_procedure('parameter_heart_rate')
param_tuples = []
for i in range(20,200,20):
    param_tuples.append((i-20,i))
hr = analyzer.calculate_parameter(complete_data.waves, complete_data.points, param_tuples ,calculate_hr,
                                  calculate_hr.default_arguments)
complete_data.add_parameter(hr, 'hr')
vis.show(complete_data, begin_time=160, end_time=240,
                             title="Wycinek <160s; 240s> z parametrem")


print(">Próba usunięcia pojedynczego punktu r i przesunięcia go obok")
vis.show(complete_data, begin_time=240, end_time=243, title="Wycinek <240s; 243s>")
complete_data.points['r'].delete_point(241) #,y=5.8)
x = 241.227

y = complete_data.waves['ecg'].value_at(x)
complete_data.points['r'].add_point(x,y)
vis.show(complete_data, begin_time=240, end_time=243, title="Wycinek <240s; 243s> z zamienionym punktem na 241s")

print(">Próba oznaczenia SBP i DBP")
find_sbp = analyzer.import_procedure('points_sbp_simple')
arguments = find_sbp.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['bp'])
found_sbp = analyzer.find_points(complete_data.waves, complete_data.points, begin_time, end_time, find_sbp, arguments)
complete_data.add_points(found_sbp, 'sbp')
find_dbp = analyzer.import_procedure('points_dbp_simple')
arguments = find_dbp.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['bp'])
found_dbp = analyzer.find_points(complete_data.waves, complete_data.points, begin_time, end_time, find_dbp, arguments)
complete_data.add_points(found_dbp, 'dbp')
vis.show(complete_data, title="Dane z odnalezionymi SBP i DBP")

print(">Próba oznaczenia DN")
find_dn = analyzer.import_procedure('points_dn_net')
arguments = find_dn.default_arguments
begin_time, end_time = complete_data.calculate_time_range(required_waves=['ecg','bp'])
found_dn = analyzer.find_points(complete_data.waves, complete_data.points, begin_time, end_time, find_dn, arguments)
complete_data.add_points(found_dn, 'dn')
vis.show(complete_data, title="Dane z odnalezionymi DN")
