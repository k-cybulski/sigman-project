"""
sigman
======
Biblioteka do manipulacji oraz analizy danych w formie przebiegu 
sygnału oraz punktów oznaczających wydarzenia w czasie (np. punkty R 
na sygnale EKG).

W tym pliku definiowane są klasy symbolizujące dane:
Wave -- rzebieg sygnału (np. sygnał EKG)
Points -- zestaw punktów (np. punkty R)
Parameter -- parametr obliczony w kilku odcinkach czasowych
Composite_data -- klasa łącząca kilka Wave oraz Points,
                  pozwalająca na wspólną analizę kilku przebiegów/
                  rodzajów punktów
"""
# TODO: Documentation should be PEP-257 compliant
from math import isclose

import numpy as np

class Wave():
    """Klasa symbolizująca przebieg sygnału. Może być on przesunięty w 
    czasie i nie zaczynać się od 0. W takim wypadku wszystkie odwołania 
    do jego wartości w danym czasie uwzględnią to przesunięcie.

    Atrybuty:
        Wave.data - tablica wartości y punktów przebiegu
        Wave.complete_length - długość przebiegu w czasie
        Wave.sample_length - długość jednego sampla
        Wave.sample_rate - częstotliwość samplowania
        Wave.wave_type - typ danych przebiegu, np. 'ecg' czy 'bp'
        Wave.offset - przesunięcie w czasie w Composite_data
    """

    def __init__(self, data, complete_length, wave_type, offset=0):
        """Inicjalizuje Wave. Przyjmuje tablicę danych wartości
        sygnału oraz jego długość, a także typ (np. 'bp').
        """
        # Okres nagranych danych; odległość w czasie między
        # punktami przebiegu.
        self.sample_length = complete_length/len(data)
        # Częstotliwość danych.
        self.sample_rate = 1/self.sample_length        
        self.complete_length = complete_length 
        self.type = wave_type 
        self.data = np.array(data) 
        self.offset = offset

    @classmethod
    def copy(cls, wave):
        """Zwraca kopię danego Wave."""
        return cls(wave.data, wave.complete_length,
                   wave_type=wave.type, offset=wave.offset)

    def __len__(self):
        """Zwraca liczbę punktów zawartych w całym ciągu danych."""
        return len(self.data)

    def sample_at(self, time):
        """Zwraca index najbliższego punktu do podanego czasu.  
        Jeśli index wystaje poza ramy czasowe danych to metoda 
        powoduje ValueError.
        """
        index = round((time-self.offset) / self.sample_length)
        # Poprawka na ostatni punkt wykresu
        if index == len(self):
            index -= 1
        if index < 0 or index > len(self):
            raise ValueError('Punkt o żądanym czasie %s wystaje poza zakres '
                             'czasowy danych' % time)
        return int(index)
    
    def value_at(self, time):
        """Zwraca wartość przebiegu w danym punkcie obliczoną za 
        pomocą interpolacji liniowej sąsiednich dwóch punktów.  Jeśli
        żądany punkt wystaje poza ramy czasowe posiadanych danych to 
        metoda wywołuje ValueError.
        """
        approx_index = (time-self.offset) / self.sample_length
        interp_index = int(approx_index)
        if interp_index < 0 or interp_index >= len(self)-1:
            raise ValueError('Punkt o żądanym czasie %s wystaje poza zakres '
                             'czasowy danych' % time)
        approx_value = np.interp(
            approx_index, [interp_index, interp_index+1], 
            [self.data[interp_index],  self.data[interp_index+1]])
        return self.data[self.sample_at(time)]
    
    def data_slice(self, begin_time, end_time, 
                   value_every=0, value_count=None):
        """Zwraca tablicę wartości danych odpowiadający żądanemu 
        zakresowi czasu.  Jeśli żądana częstotliwość jest inna niż 
        bazowa, to  zwrócony ciąg jest wynikiem interpolacji liniowej 
        posiadanych już danych.

        Argumenty:
        begin_time - początek zakresu
        end_time - koniec zakresu
        value_every - żądana częstotliwość punktów (odstęp czasowy 
                      między punktami) wytworzonej tablicy. Jeśli
                      wynosi 0, to zwraca punkty o takiej samej
                      częstotliwości jak bazowy Wave.
        value_count - ile ma być punktów w zwróconym ciągu. Jeśli 
                      i value_count i value_every są ustawione, 
                      priorytetem jest value_count.
        """
        begin_i = self.sample_at(begin_time)
        end_i = self.sample_at(end_time)
        # Sprawdzamy czy akurat częstotliwość bazowa i żądana się 
        # nakładają
        if value_count is not None:
            value_every = (end_time-begin_time)/value_count
        if value_every == 0 or isclose(self.sample_length, value_every):
           return self.data[begin_i:end_i]
        # Jeśli żądana częstotliwość punktów na wykresie jest inna niż
        # bazowa, należy przeprowadzadzić interpolacjaę liniową na 
        # żądanych punktach czasowych
        wanted_values = np.arange(begin_time, end_time, value_every)
        coord_x, coord_y = self.generate_coordinate_tables(
            begin_time = begin_time, end_time = end_time, 
            begin_x = begin_time)
        interpolated_table = np.interp(wanted_values, coord_x, coord_y)
        return interpolated_table

    def replace_slice(self, begin_time, end_time, wave):
        """Zastępuje wybrany zakres wartości przebiegu wartościami 
        innego Wave, np przefiltrowanego.  Podany Wave 
        musi mieć taką samą częstotliwość danych jak bazowy.

        Argumenty:
        begin_time - początek zakresu czasowego punktów do zastąpienia
        end_time - koniec zakresu czasowego punktów do zastąpienia
        wave - Wave, którego danymi mamy zastąpić dany fragment
        """
        # TODO: Dodać możliwość przyjmowania danych o innej częstotliwości
        # zmieniając je tak by pasowały?
        if not isclose(self.sample_length,
                       wave.sample_length, rel_tol=0.0001):
            raise ValueError('Fragment do wklejenia ma częstotliwość danych '
                             'niezgodną z częstotliwością danych całości')
        if end_time - begin_time > wave.complete_length:
            raise ValueError('Dany Wave krótszy niż zakres czasu danych '
                             'do zastąpienia')
        begin_i = self.sample_at(begin_time)
        end_i = self.sample_at(end_time)
        for j in range(end_i-begin_i):
            self.data[begin_i+j]=wave.data[j]
    
    def generate_coordinate_tables(self, begin_time=0, end_time=None,
                                   begin_x=0):
        """Zwraca wszystkie punkty przebiegu w formie dwóch tablic - 
        wartości x oraz wartości y. Przydatne do wizualizacji.

        Argumenty:
        begin_time - początek zakresu czasowego punktów do zwrócenia 
                     w tablicy
        end_time - koniec zakresu czasowego punktów do zwrócenia w 
                   tablicy
        begin_x - wartość x pierwszego punktu na tablicy
        """
        data = self.data_slice(begin_time, end_time)
        output_x = []
        output_y = []
        for i in range(len(data)):
            output_x.append(begin_x+i * self.sample_length)
            output_y.append(data[i])
        output_x = np.array(output_x)
        output_y = np.array(output_y)
        return output_x, output_y

class Points():
    """Klasa symbolizująca zestaw punktów jednego typu (np. R).
    Przechowuje je w dwóch tablicach - wartości x i y wszystkich
    punktów, posortowanych według x.

    Atrybuty:
        Points.data_x - tablica wartości x punktów
        Points.data_y - tablica wartości y punktów
        Points.point_type - typ punktów, np. 'r' czy 'sbp' 
    """

    def __init__(self, data_x, data_y, point_type):
        """Inicjalizuje Points. Przyjmuje dwie tablice x i y
        punktów, a także typ punktów (np. 'r').
        """
        # sortowanie by punkty były po kolei
        temp_data_x, temp_data_y = zip(*sorted(zip(data_x,data_y)))
        self.data_x = np.array(temp_data_x) 
        self.data_y = np.array(temp_data_y) 
        self.type = point_type 
    
    @classmethod
    def copy(cls, points):
        return cls(points.data_x, points.data_y,
                   point_type = points.type)

    def __len__(self):
        return len(self.data_x)

#   def __getitem__(self, key):
#       x = self.data_x[key]
#       y = self.data_y[key]
#       points = np.vstack((x,y))
#       return points

    def slice_range(self, begin_time, end_time):
        """Zwraca range indeksów punktów, które znajdują się w danym
        zakresie czasowym. 
        """
        begin_i = np.searchsorted(self.data_x, begin_time)
        end_i = np.searchsorted(self.data_x, end_time)
        # Sprawdzamy czy jest choć jeden punkt
        if begin_i != end_i:
            return range(begin_i, end_i)
        else:
            return None

    def data_slice(self, begin_time, end_time, left_offset=0):
        """Zwraca tablice współrzędnych x oraz y punktów w danym 
        zakresie czasu.

        Argumenty:
        left_offset - ile punków dodatkowych w lewo, przed zakresem,
                      podać.
        """
        temp_range = self.slice_range(begin_time, end_time)
        if temp_range is None:
            return None
        begin_i = temp_range[0] - left_offset
        if begin_i < 0:
            begin_i = 0
        end_i = temp_range[-1]+1
        return self.data_x[begin_i:end_i], self.data_y[begin_i:end_i]

    
    def delete_slice(self, begin_time, end_time):
        """Usuwa punkty w danym zakresie czasu. Zwraca index miejsca
        współrzędnych tablic gdzie były usunięte punkty.
        """
        temp_range = self.slice_range(begin_time, end_time)
        self.data_x = np.delete(self.data_x, temp_range)
        self.data_y = np.delete(self.data_y, temp_range)
        return temp_range[0]

    def replace_slice(self, begin_time, end_time, points):
        begin_i = self.delete_slice(begin_time, end_time)
        """Zastępuje punkty na danym zakresie czasu innym Points.
        """
        # Teraz wszystkie punkty z points które nie wychodzą poza 
        # ramy czasowe podane w argumentach funkcji wkładamy do wlasnych
        # tablic współrzędnych
        j = 0
        while (j < len(points) and 
                points.data_x[j] < end_time-begin_time):
            np.insert(self.data_x, begin_i+j, points.data_x[j]+begin_time)
            np.insert(self.data_y, begin_i+j, points.data_y[j])
    
    def add_point(self, x, y):
        """Dodaje punkt."""
        i = np.searchsorted(self.data_x, x)
        self.data_x=np.insert(self.data_x, i, x)
        self.data_y=np.insert(self.data_y, i, y)
        
    def add_points(self, points, begin_time=0):
        """
        Dodaje wszystkie punkty z danego Points do siebie.
        
        Argumenty:
        points - Points do dodania do siebie
        begin_time - czas, od którego mają być dodawane wszystkie punkty;
                     np. jeśli dodawany points z własnej perspektywy 
                     zaczyna się na 0 sekundzie gdy naprawdę jest gdzieś 
                     głęboko w wykresie.
        """
        for x, y in zip(points.data_x, points.data_y):
            self.add_point(x+begin_time, y)

    def delete_point(self, x, y=None):
        """Usuwa punkt najbliższy do danych współrzędnych. Argument
        y jest opcjonalny, ponieważ wiekszosść punktów na przebiegach
        symbolizują wydarzenia w czasie i ich y są mniej ważne.
        """
        if y is not None:
            closest_id = self.closest_point_id(x, y)
        else:
            closest_id = np.argmin(np.abs(self.data_x - x))
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
    
    def move_point(self, x1, y1, x2, y2):
        closest_id = self.closest_point_id(x1, y1)
        if not (isclose(self.data_x[closest_id], x1) and
                isclose(self.data_y[closest_id], y1)):
            raise ValueError('Nie ma punktu o takich x1 i y1')
        # Powtarzamy się tutaj by nie wywoływać funkcji, które w QtSigman
        # mogą wywołać rysowanie od zera
        self.data_x = np.delete(self.data_x, closest_id)
        self.data_y = np.delete(self.data_y, closest_id)
        i = np.searchsorted(self.data_x, x2)
        self.data_x=np.insert(self.data_x, i, x2)
        self.data_y=np.insert(self.data_y, i, y2)

    def closest_point_id(self, x, y):
        points = np.vstack((self.data_x, self.data_y))
        point = np.array([[x,y]])
        comparison_distances = np.sum((points - point)**2, axis=1)
        return np.argmin(comparison_distances) 

    def align_to_line(self, wave):
        """Wyrównuje współrzędne y punktów do y danego Wave."""
        for i in range(len(self)):
            self.data_y[i] = wave.value_at(self.data_x[i])

    def move_in_time(self, time):
        """Przesuwa punkty w czasie."""
        for i in range(len(self)):
            self.data_x[i] += time

class Parameter():
    """Parameter jest klasą odpowiadającą za przechowywanie kilku 
    obliczonych wartości parametru tego zamego typu, wraz z informacjami
    czasowymi w formie list początkowych i końcowych czasów. Parametry 
    powstają jako wynik działania procedur.
    
    Atrybuty:
        self.parmaeter_begin_times - tablica czasów początkowych parametrów
        self.parameter_end_times - tablica czasów końcowych parametrów
        self.parameter_values - tablica wartości parametru
    """

    def __init__(self, parameter_type):
        self.type = parameter_type
        self.begin_times = np.array([])
        self.end_times = np.array([])
        self.values = np.array([])

    @classmethod
    def copy(cls, parameter):
        out = cls(parameter.type)
        out.begin_times = np.copy(parameter.begin_times)
        out.end_times = np.copy(parameter.end_times)
        out.values = np.copy(parameter.values)
        return out

    def __len__(self):
        return len(self.begin_times)

    def add_value(self, begin_time, end_time, value):
        """Dodaje wartość parametru obliczoną w danym czasie"""
        if len(self)==0: 
            self.begin_times = np.append(self.begin_times, begin_time)
            self.end_times = np.append(self.end_times, end_time)
            self.values = np.append(self.values, value)
        else:
            i = np.searchsorted(self.begin_times, begin_time)
            self.begin_times = np.insert(self.begin_times, i, begin_time)
            self.end_times = np.insert(self.end_times, i, end_time)
            self.values = np.insert(self.values, i, value)

    def contained_in(self, time):
        """Zwraca indeksy wartości parametru, które zawierają dany punkt
        czasu w sobie.
        """
        contained_indices = []
        for index, begin_time, end_time in zip(range(len(self)),self.begin_times,
                                        self.end_times):
            if time >= begin_time and time <= end_time:
                contained_indices.append(index)
            elif time > begin_time:
                break
        return contained_indices

    def value_at(self, time):
        """Zwraca wartość parametru w danym czasie."""
        parameter_indices = self.contained_in(time)
        if len(parameter_indices) == 0:
            return None
        else:
            return np.average(self.values[parameter_indices])

    def generate_parameter_line_tuples(self, begin_time=None, end_time=None):
        """Zwraca tuple wartości x i y w układzie współrzędnych, by
        później mogły one zostać wizualizowane.
        """
        line_tuples = []
        for param_begin_time, param_end_time, value in zip(self.begin_times,
                                                           self.end_times,
                                                           self.values):
            if begin_time is not None and param_end_time < begin_time:
                continue
            if end_time is not None and param_begin_time > end_time:
                break
            temp_begin_time = max(begin_time, param_begin_time)
            temp_end_time = min(end_time, param_end_time)
            line_tuples.append(((temp_begin_time, temp_end_time),(value, value)))
        return line_tuples

class Composite_data:
    """Obiekt przchowujący komplet Wave, Points oraz Parameter
    który pozwala na przeprowadzanie operacji na nich wszystkich
    jednocześnie. Procedury analizy przyjmują Composite_data jako
    argument.

    Wszystkie dane przechowywane są w Composite_data w trzech dict:
        self.waves
        self.points
        self.parameters
    """

    def __init__(self, waves=None, points=None, parameters=None):
        self.waves = {}
        self.points = {}
        self.parameters = {}
        if waves is not None: 
            self.waves = waves
        if points is not None: 
            self.points = points
        if parameters is not None:
            self.parameters = parameters

    def calculate_complete_time_span(self):
        """Zwraca początek oraz koniec zakresu czasowego w sekundach,
        na długości którego dostępne są dane jakiekogolwiek przebiegu.
        """
        begin_time = None
        end_time = None
        for key, wave in self.waves.items():
            if begin_time is None:
                begin_time = wave.offset
            else:
                begin_time = min(wave.offset, begin_time)
            if end_time is None:
                end_time = wave.offset + wave.complete_length
            else:
                end_time = max(wave.offset + wave.complete_length,
                               end_time)
        for key, points in self.points.items():
            if begin_time is None:
                begin_time = points.data_x[0]
            else:
                begin_time = min(points.data_x[0], begin_time)
            if end_time is None:
                end_time = points.data_x[-1]
            else:
                end_time = max(points.data_x[-1],
                               end_time)
        if begin_time and end_time is None:
            begin_time = 0
        return begin_time, end_time

    def calculate_time_range(self, required_waves):
        """Zwraca początek oraz koniec zakresu czasowego w sekundach,
        na długości którego dostępne są dane wszystkich wymaganych 
        przebiegów.
        """
        begin_time = None
        end_time = None
        for required_wave in required_waves:
            wave = self.waves[required_wave]
            if begin_time is None:
                begin_time = wave.offset
            else:
                begin_time = max(wave.offset, begin_time)
            if end_time is None:
                end_time = wave.offset + wave.complete_length
            else:
                end_time = min(wave.offset + wave.complete_length,
                               end_time)
        return begin_time, end_time

    def add_wave(self, wave, dict_type, replace=False):
        """Dodaje przebieg."""
        if dict_type is None:
            dict_type = wave.type
            if dict_type is None:
                raise ValueError('Etykieta (dictionary key; tutaj dict_type) '
                                 'linii danych nie może być pusta')
        if dict_type in self.waves and not replace:
            raise ValueError('Etykieta %s w waves jest już zajęta.' 
                             % dict_type)
        self.waves[dict_type] = wave

    def delete_wave(self, dict_type):
        """Usuwa przebieg."""
        self.waves.pop(dict_type)

    def add_points(self, points, dict_type, join=False):
        """Dodaje zestaw punktów."""
        # TODO: czy defaultowo join powinno być False?
        if dict_type is None:
            dict_type = points.type
        if dict_type in self.points:
            if join:
                self.points[dict_type].add_points(points)
            else:
                raise ValueError('Etykieta %s w points jest już zajęta.'
                                 % dict_type)
        else:
            self.points[dict_type] = points

    def delete_points(self, dict_type):
        """Usuwa zestaw punktów."""
        self.points.pop(dict_type)

    def add_parameter(self, parameter, dict_type, replace=False):
        """Dodaje parametr."""
        if dict_type is None:
            dict_type = parameter.type
            if dict_type is None:
                raise ValueError('Etykieta (dictionary key; tutaj dict_type) '
                                 'parametru nie może być pusta')
        if dict_type in self.parameters and not replace:
            raise ValueError('Etykieta %s w parameters już zajęta.' 
                             % dict_type)
        self.parameters[dict_type] = parameter

    def delete_parameter(self, dict_type):
        """Usuwa parametr."""
        self.parameters.pop(dict_type)
