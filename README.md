# sigman-project
Celem tego projektu jest utworzenie otwartej i dobrze udokumentowanej biblioteki **sigman** pozwalającej na dowolną analizę danych biomedycznych za pomocą prostych do utworzenia zewnętrznych procedur, a także aplikacji **QtSigman** która pozwoli na korzystanie z tej biblioteki przez interfejs graficzny.


## Instalacja
### Technologie i biblioteki
* [Python 3](https://www.python.org/about/) - całość
* [NumPy](http://www.numpy.org/) - podstawowa obsługa danych
* [SciPy](https://scipy.org/) - filtry/dodatkowe funkcje do analizy
* [matplotlib](http://matplotlib.org/) - wizualizacja wykresów
* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI
* [XlsxWriter](https://github.com/jmcnamara/XlsxWriter) - Zapisywanie plików .xlsx

### Linux
#### Ubuntu
```
git clone "https://github.com/k-cybulski/sigman-project.git"
sudo apt install python3-pip
pip3 install PyQt5 numpy scipy matplotlib XlsxWriter
```

## Obsługa
### sigman
Poniższe przykłady zakładają importowanie `sigman` jako `sm`, a `sigman.file_manager` jako `fm`.

#### sm.Wave
Podstawowym rodzajem danych w bibliotece sigman jest przebieg `sm.Wave` (*z ang. waveform*) . Określony jest on przede wszystkim tablicą danych `Wave.data` oraz całkowitym czasem trwania `Wave.complete_length`. Do późniejszej analizy ważny będzie także typ przebiegu `Wave.type` określający rodzaj danych, np. `ecg` czy `bp`.

Obiekty `sm.Wave` można importować za pomocą funkcji `fm.import_line`.

```python
from sigman import file_manager as fm
ecg = fm.import_wave('example_data/EKG.dat')
```

#### sm.Points
Punkty oznaczające wydarzenia w czasie o danej wartości, np. R na przebiegu EKG, symbolizowane są klasą `sm.Points`. Zawiera on dwie tablice `Points.data_x` oraz `Points.data_y` posortowane w kolejności `data_x`, a także typ punktów jak `r`.

Punkty można importować
```python
from sigman import file_manager as fm
r = fm.import_points('example_data/R.dat')
```
lub odnajdywać za pomocą procedur, co zostanie wytłumaczone dogłębniej potem.

#### sm.Parameter
Klasa zawierająca kilka obliczonych wartości `Parameter.values` parametru, np. heart rate, a także informacje o tym od jakiego czasu `Parameter.begin_times`  do jakiego `Parameter.end_times` są one obliczone. Tworzy się je tylko wykorzystując procedury.

#### sm.Composite_data
Klasa łącząca kilka powyższych danych w jedną spójną całość. Może zawierać nieokreśloną liczbę `sm.Wave`, `sm.Points` oraz `sm.Parameter`. Pozwala stosować procedury korzystające z kilku różnych danych, np. procedurę odnajdującą wcięcia dykrotyczne w oparciu o SBP i przebiegi BP oraz EKG.

Dane przechowuje w trzech `dict`:
* `Composite_data.waves`
* `Composite_data.points`
* `Composite_data.parameters`

Dodawać je można i przy inicjalizacji i już po zainicjalizowaniu.
```python
import sigman as sm
from sigman import file_manager as fm

ecg = fm.import_wave('example_data/EKG.dat')
composite_data = sm.Composite_data(waves={'ecg':ecg})

bp = fm.import_wave('example_data/BP.dat')
composite_data.add_wave(bp, 'bp')
r = fm.import_points('example_data/R.dat')
composite_data.add_points(r, 'r')
```

`file_manager` zawiera też funkcje pozwalające zapisywać `sm.Composite_data` na potem.
```python
fm.save_composite_data('temporary_save.pickle', composite_data)
```
oraz
```python
composite_data = fm.load_composite_data('temporary_save.pickle')
```

Obecnie wykorzystuje to moduł pythonowy `pickle`, choć jest w planach w przyszłości zamienić go na coś bezpieczniejszego.

#### sigman.visualizer
Biblioteka sigman zawiera moduł `visualizer` pozwalający na bardzo proste lecz dość ograniczone wizualizowanie `sm.Composite_data`. Po wykonaniu powyższego kodu tworzącego composite_data można spróbować:
```python
from sigman import visualizer as vis
vis.visualize_composite_data(composite_data)
```
`visualizer` pozwala także na wizualizację tylko wycinka czasowego, czy też tylko wybranych danych z `sm.Composite_data`.
```python
vis.visualize_composite_data(composite_data, begin_time=40, end_time=60, wanted_waves=['ecg'], title="Wykres EKG") 
```

#### sigman.analyzer
Moduł `analyzer` pozwala na stosowanie zewnętrznych procedur z folderu `sigman-project/procedures` na danych. Ich dokładna struktura i całokształt opisany jest głębiej w samym pliku modułu.

Zakładany sposób wykorzystania procedur polega na zaimportowaniu, zmianie wybranych argumentów z `procedure.default_arguments`, użyciu ich oraz dodaniu/zamiany danych w `sm.Composite_data` na nowe.

Przykład filtrowania wycinka przebiegu EKG.
```python
import sigman as sm
from sigman import file_manager as fm
from sigman import analyzer

ecg = fm.import_wave('example_data/EKG.dat')
composite_data = sm.Composite_data(waves={'ecg':ecg})

butterworth = analyzer.import_procedure('modify_filter_butterworth')
arguments = butterworth.default_arguments
arguments['N'] = 3
arguments['Wn'] = 30
filtered_wave = analyzer.modify_wave(composite_data.waves['ecg'], 20, 60, butterworth, arguments)
composite_data.waves['ecg'].replace_slice(20,60, filtered_wave)
```

Przykłady użycia różnych funkcji biblioteki w pliku `test_sigman.py`. Dokładniejszy opis wkrótce.

### QtSigman
Należy uruchomić skrypt `run_qtsigman.py`.

## Stan obecny
### sigman
Biblioteka nadaje się do wstępnego użytku. Obecnie ważne jest napisanie większej liczby procedur.
- [ ] Wczytywanie danych
  - [x] z plików `.dat`
  - [ ] z signalyzera
- [ ] Zapisywanie danych
  - [x] sygnałów / punktów w plikach `.dat`
  - [x] całych projektów / niedokończonej pracy
  - [ ] obliczonych parametrów w `.xslx` / `.csv`
- [x] Operowanie na danych
  - [x] obróbkę danych na odcinkach czasowych zewnętrznymi procedurami
    - [x] filtracja / modyfikacja sygnału
    - [x] wykrywanie punktów
    - [x] obliczanie średnich parametrów
  - [x] usuwanie i dodawanie pojedynczych punktów
  - [x] przesuwanie przebiegów i punktów względem siebie w czasie
- [x] Wizualizacja danych
  - [x] prosty mechanizm wizualizacji przebiegów, punktów i parametrów

### QtSigman
Aplikacja wymaga pracy nim będzie w stanie użytkowym.
- [ ] Główne okno
  - [ ] wykres danych
    - [x] przebiegi
    - [x] punktowy
    - [x] parametry *do uzgodnienia*
    - [ ] interaktywność
      - [x] skalowanie
      - [x] przesuwanie
      - [x] ukrywanie i pokazywanie elementów
      - [ ] sprawdzanie dokładnych wartości
      - [ ] manualna edycja punktów
  - [ ] listy obiektów
    - [x] przebiegi
    - [x] punkty
    - [ ] parametry
    - [ ] interaktywność
      - [x] edycja metainformacji
      - [ ] tryb edycji punktów
    - [ ] wyświetlanie metainformacji o danych na listach
- [ ] Obsługa plików
  - [x] importowanie przebiegów i punktów
  - [ ] eksportowanie przebiegów i punktów
  - [x] zapisywanie i wczytywanie projektu
- [ ] Obsługa procedur
  - [x] modyfikacja przebiegów
  - [x] odnajdywanie punktów
  - [ ] obliczanie parametrów
  - [ ] przeprowadzanie całościowej analizy (kilka procedur na raz)
  - [ ] wizualizacja wyniku działania procedury przed potwierdzeniem

## Standardy kodu
Kod projektu powinien być utrzymywany jak najbliżej norm [PEP-8](https://www.python.org/dev/peps/pep-0008/). W bibliotece sigman utrzymywane jest nazewnictwo `lowercase_with_underscores`, natomiast w kodzie aplikacji QtSigman w ramach konsystencji z biblioteką PyQt5 wykrozystywane jest nazewnictwo `CamelCase`.

Obecnie dokumentacja jest po polsku, natomiast zostanie ona przetłumaczona na angielski dla szerszego odbioru.

## Podziękowania
* [Instytut Medycyny Doświadczalnej i Klinicznej im. M. Mossakowskiego PAN](http://imdik.pan.pl/pl/) - wsparcie i nakierowanie projektu, dane
