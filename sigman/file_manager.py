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

def open_composite_data(file_name):
    """Otwiera zapisany w .pickle Composite_data."""
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


def _import_line_dat(file_name, line_type='default', offset=0):
    """Importuje ciąg danych o stałej częstotliwości z pliku .dat i
    zwraca odpowiadający mu sm.Data_line.
    """
    x, y = _import_dat(file_name)
    complete_len = x[-1]
    return sm.Data_line(y, complete_len, 
                        line_type = line_type, 
                        offset = offset)
    
def _import_point_dat(file_name, point_type='default'):
    """Importuje współrzędne punktów z pliku .dat i zwraca odpowiadający
    im sm.Data_points.
    """
    x, y = _import_dat(file_name)    
    return sm.Data_points(x, y, 
                          point_type = point_type)

def import_line(file_name, line_type='default', offset=0):
    """Importuje dane liniowe z danego pliku, przy czym wybiera
    odpowiednią funkcję do formatu danego pliku.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_line_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    return import_func(
        file_name, 
        line_type = line_type, 
        offset = offset)

def import_points(file_name, point_type='default'):
    """Importuje punkty z danego pliku, przy czym wybiera odpowiednia
    funkcję formatu danego pliku.
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

def _export_line_dat(file_name, data_line):
    """Eksportuje Data_line do pliku o formacie .dat."""
    data_x, data_y = data_line.generate_coordinate_tables()
    _export_dat(data_x,data_y,file_name)

def _export_point_dat(file_name, data_points):
    """Eksportuje Data_points do pliku o formacie .dat."""
    _export_dat(file_name, data_points.data_x, data_points.data_y)

def export_line(file_name, data_line):
    """Eksportuje Data_line do pliku, wykorzystując przy tym funkcję
    odpowiednią dla pożądanego formatu.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_line_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    export_func(file_name, data_line)

def export_points(file_name, data_points):
    """Eksportuje Data_points do pliku, wykorzystując przy tym funkcję
    odpowiednią dla pożądanego formatu.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        export_func = _export_point_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    export_func(file_name, data_points)
