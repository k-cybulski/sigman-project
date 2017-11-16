"""
W tym pliku zawarte są funkcje służące do zapisywania i wczytywania
danych do analizy.
"""
# TODO: save_composite_data oraz open_composie_data nie powinny korzystać z pickle; jest wolny, może kreować masywne pliki przy wielkich ilościach danych oraz jest niebezpieczny - pozwala na uruchamianie kodu bez wiedzy podczas włączania


import csv
import os.path
import pickle

import numpy as np

import sigman as sm 

def save_composite_data(file_name, composite_data):
    """Zapisuje dany Composite_data w pliku .pickle."""
    with open(file_name, 'wb') as pickle_file:
        pickle.dump(composite_data, pickle_file)

def load_composite_data(file_name):
    """Wczytuje zapisany w .pickle Composite_data."""
    with open(file_name, 'rb') as pickle_file:
        return pickle.load(pickle_file)

def _import_dat(file_name):
    """Importuje dwie tablice współrzędnych z pliku .dat."""
    x = []
    y = []
    with open(file_name) as csv_file:
        reader = csv.reader(csv_file, delimiter=' ')
        for row in reader:
            x.append(float(row[0]))
            # Niektóre pliki .dat mają dwie spacje zamiast jednej.
            # W takim wypadku to row[1] będzie pusty
            if row[1]=="": 
                y.append(float(row[2]))
            else:
                y.append(float(row[1]))
    return x, y


def _import_line_dat(file_name, wave_type='default', offset=0):
    """Importuje przebieg o stałej częstotliwości z pliku .dat i
    zwraca odpowiadający mu sm.Wave.
    """
    x, y = _import_dat(file_name)
    complete_len = x[-1]
    return sm.Wave(y, complete_len, 
                        wave_type = wave_type, 
                        offset = offset)
    
def _import_point_dat(file_name, point_type='default'):
    """Importuje współrzędne punktów z pliku .dat i zwraca odpowiadający
    im sm.Points.
    """
    x, y = _import_dat(file_name)    
    return sm.Points(x, y, 
                          point_type = point_type)

def import_line(file_name, wave_type='default', offset=0):
    """Importuje przebieg z danego pliku, przy czym wybiera odpowiednią
    funkcję do formatu danego pliku.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_line_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    return import_func(
        file_name, 
        wave_type = wave_type, 
        offset = offset)

def import_points(file_name, point_type='default'):
    """Importuje punkty z danego pliku, przy czym wybiera odpowiednią
    funkcję do formatu danego pliku.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_point_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    return import_func(
        file_name,
        point_type = point_type)

def _export_dat(data_x,data_y,filename):
    """Zapisuje dwie tablice współrzędnych w pliku .dat."""
    with open(filename, 'w') as csv_file:
        writer = csv.writer(csv_file, delimiter=' ')
        for x, y in zip(data_x, data_y):
            writer.writerow([x,y])

def _export_line_dat(file_name, wave):
    """Eksportuje Wave do pliku o formacie .dat."""
    data_x, data_y = wave.generate_coordinate_tables()
    _export_dat(data_x,data_y,file_name)

def _export_point_dat(file_name, points):
    """Eksportuje Points do pliku o formacie .dat."""
    _export_dat(file_name, points.data_x, points.data_y)

def export_line(file_name, wave):
    """Eksportuje Wave do pliku, wykorzystując przy tym funkcję
    odpowiednią dla pożądanego formatu.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_line_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    export_func(file_name, wave)

def export_points(file_name, points):
    """Eksportuje Points do pliku, wykorzystując przy tym funkcję
    odpowiednią dla pożądanego formatu.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_point_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    export_func(file_name, points)
