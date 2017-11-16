# sigman-project
Celem tego projektu jest utworzenie biblioteki **sigman** pozwalającej na dowolną analizę danych biomedycznych za pomocą prostych do utworzenia zewnętrznych procedur, a także aplikacji **QtSigman** która pozwoli na korzystanie z tej biblioteki przez interfejs graficzny.


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
cd sigman-project
sudo apt install python3-pip
pip3 install PyQt5 numpy scipy matplotlib XlsxWriter
```

## Obsługa
### sigman
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
