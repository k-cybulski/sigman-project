# sigman-project
Celem tego projektu jest utworzenie biblioteki (sigman) pozwalającej na dowolną
analizę danych biomedycznych za pomocą prostych do utworzenia zewnętrznych 
procedur, a także programu (QtSigman) który pozwoli na korzystanie z tej 
biblioteki przez interfejs graficzny.

## Cele
1. sigman
1) Wczytywanie i zapisywanie danych                 [ ]
    = wczytywanie                                   [ ]
        - z plików .dat                             [x]
        - z sequence analyzera                      [ ]
    = zapisywanie                                   [ ]
        - przefiltrowanych danych liniowych / punktowych w plikach .dat [x]
        - całych projektów / niedokończonej pracy   [x]
        - parametrów w .xlsx / .csv                 [ ]
2) Operowanie na danych                             [x]
    = obróbkę danych na odcinkach czasowych         [x]
        - filtracja                                 [x]
        - wykrycie punktów                          [x]
        - obliczanie parametrów                     [x]
        - wykonywanie analizy całościowej           [ ]
    = manualną edycję i poprawki wykrytych punktów  [x]
    = przesuwanie przebiegów względem siebie w czasie   [x]
3) Wizualizacja danych                              [x]
    = proste ukazywanie wszystkich elementów danych [x]
        - przebiegi                                 [x]
        - punkty                                    [x]
        - parametry                                 [x]
2. QtSigman                                         [ ]
1) Główne okno                                      [ ]
    = Główny wykres                                 [ ]
        - przebiegi                                 [x]
        - punkty                                    [x]
        - parametry                                 [x]
        - interaktywność                            [ ]
            > skalowanie                            [x]
            > przemieszczanie                       [x]
            > ukrywanie i pokazywanie elementów     [x]
            > sprawdzanie dokładnych wartości       [ ]
            > usuwanie i dodawanie punktów          [ ]
    = Listy obiektów                                [x]
        - przebiegi                                 [x]
        - punkty                                    [x]
        - parametry                                 [ ]
        - interaktywność                            [x]
            > okno edycji metainformacji            [x]
2) Obsługa plików                                   [ ]
    = Importowanie                                  [x]
        - przebiegów                                [x]
        - punktów                                   [x]
    = Eksportowanie                                 [ ]
        - przebiegów                                [ ]
        - punktów                                   [ ]
        - parametrów                                [ ]
    = Zapisywanie projektu                          [x]
    = Wczytywanie projektu                          [x]
3) Obsługa procedur                                 [ ]
    = Bazowe okno procedury                         [ ]
    = Filtrowanie przebiegów                        [ ]
    = Odnajdywanie punktów                          [ ]
    = Obliczanie parametrów                         [ ]
    = Przeprowadzanie całościowej analizy           [ ]

## Standardy kodu
Kod projektu powinien być utrzymywany jak najbliżej norm PEP-8 (zawarte są 
w pliku PEP-8-style-guide.pdf). W bibliotece sigman utrzymywane jest
nazewnictwo lowercase_with_underscores, natomiast w kodzie programu QtSigman 
w ramach konsystencji z biblioteką PyQt5 wykorzystywane jest nazewnictwo
CamelCase.

## Technologie i biblioteki
* Python 3 - Całość
* csv - Zapisywanie i otwieranie plików .dat
* pickle - Zapisywanie i otwieranie projektów
* PyQt5 - GUI
* matplotlib - Wizualizacja wykresów 
* NumPy - Obsługa danych
* SciPy - Filtracja/dodatkowe funkcje
* XlsxWriter - Zapisywanie plików .xlsx

## Autorzy
* Krzysztof Cybulski - k.cybulski.dev@gmail.com
