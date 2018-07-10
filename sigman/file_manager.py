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


def _import_wave_dat(file_name, wave_type, offset=0):
    """Importuje przebieg o stałej częstotliwości z pliku .dat i
    zwraca odpowiadający mu sm.Wave.
    """
    x, y = _import_dat(file_name)
    complete_len = x[-1]
    return sm.Wave(y, complete_len, 
                        wave_type = wave_type, 
                        offset = offset)
    
def _import_point_dat(file_name, point_type):
    """Importuje współrzędne punktów z pliku .dat i zwraca odpowiadający
    im sm.Points.
    """
    x, y = _import_dat(file_name)    
    return sm.Points(x, y, 
                          point_type = point_type)

def import_wave(file_name, wave_type, offset=0):
    """Importuje przebieg z danego pliku, przy czym wybiera odpowiednią
    funkcję do formatu danego pliku.
    """
    extension = os.path.splitext(file_name)[1][1:]
    if extension == 'dat':
        import_func = _import_wave_dat
    else:
        raise ValueError("Nieodpowiedni format plików")
    return import_func(
        file_name, 
        wave_type = wave_type, 
        offset = offset)

def import_points(file_name, point_type):
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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
   
def import_data_from_modelflow(file_name):
    x = []
    y = []
    names = []
    with open(file_name) as f:
       if '.A00' in file_name:
           flag = False
           for line in f:
               if "END preamble" in line:
                  flag = True        
               if flag:
                   pom = line.split()              
                   if len(pom) > 2:
                       if is_number(pom[0]):
                           x.append(float(pom[0]))  
                           if (len(y)<len(pom)):
                                 y = [[0 for i in range(1)] for j in range(len(pom))]
                                 for i in range(1, len(pom)):
                                     y[i-1][0]=(float(pom[i]))                                          
                           else:
                               for i in range(1, len(pom)):
                                    y[i-1].append(float(pom[i]))
                       else:
                           if len (names)<1:
                               names = pom
       else:
           i = 0
           for line in f:
               i = i + 1
               if i == 8:
                   pom = line.split(';')
                   if '\n' in pom:
                       del pom[pom.index('\n')]
                   names = pom
               if i > 8:
                   pom = line.split(';') 
                   if '\n' in pom:
                       del pom[pom.index('\n')]
                   if len(pom) > 2:
                       if is_number(pom[0]):
                           x.append(float(pom[0]))  
                           if (len(y)<len(pom)):#W pierwszej iteracji tablica jest tworzona
                                 y = [[0 for k in range(1)] for j in range(len(pom))]
                                 for k in range(1, len(pom)):
                                     if (is_number(pom[k])):
                                         y[k-1][0]=(float(pom[k]))   
                                     else:
                                         y[k-1][0] = 0
                           else:#W kolejnych uzupełniana
                               for k in range(1, len(pom)):
                                    if (is_number(pom[k])):
                                         y[k-1].append(float(pom[k]))   
                                    else:
                                         y[k-1].append (0)
       if len(y[len(y)-1])< len(y[1]):
           del y[len(y)-1]
    return x, y, names


def import_signal_from_signal_express_file (file_name):
    x = []
    y = []
    names = []
    dt = 0
    with open(file_name,encoding="CP1250") as f:
        i = 1
        for line in f:
            if (i == 1):
                if 'channel names:' not in line:
                    break;
            if (i == 2):
                pom = line.split ('	')
                for name in pom:
                    names.append (name[(name.rfind('-')+2):].replace('\n',''))
            if (i == 6):
                dt = float(line.replace (',','.'))
            if (i > 7):
                signals_value = line.split ('	')
                nr = 0
                if len(y) == 0:
                    y = [[0 for k in range(1)] for j in range(len(pom))]
                for value in signals_value:
                    if (i == 8):
                        y[nr][0]=(float(value.replace (',','.')))
                    else:
                        y[nr].append(float(value.replace (',','.')))
                    nr = nr + 1
            i= i + 1
    for i in range(0,len(y[0])):
        x.append (i*dt)
    return x, y, names