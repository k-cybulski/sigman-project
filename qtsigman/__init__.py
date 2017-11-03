"""
qtSigman
======
Biblioteka tworząca GUI w PyQt5 do bezpośredniej współpracy z 
biblioteką sigman.

Tutaj utrzymujemy nazewnictwo camelCase na tyle na ile to możliwe ze
względu na zgodność z biblioteką PyQt5.
"""
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC
import sigman as sm
from matplotlib import colors

from qtsigman.defaultColors import defaultColors
from qtsigman import mplWidgets

#TODO: Needed stuff:
#klasa wykresu
#klasa obiektu listy linii
#klasa listy linii
#klasa obiektu listy punktów
#klasa listy punktów
#klasa obiektu listy parametrów
#klasa listy parametrów

class CompositeDataWrapper(sm.Composite_data):
    """Klasa rozszerzająca sm.Composite_data o zmienne i funkcje 
    pozwalające na wykorzystanie go graficznie."""
    def __init__(self, **kwargs):
        super(CompositeDataWrapper, self).__init__(**kwargs)
        self.lineColors = {}
        self.pointColors = {}
        self.parameterColors = {}
        for key in self.data_lines:
            self.lineColors[key] = colors.to_hex(defaultColors[key])
        for key in self.data_points:
            self.pointColors[key] = colors.to_hex(defaultColors[key])
        for key in self.parameters:
            self.parameterColors[key] = colors.to_hex(defaultColors[key])
        self.leftAxisLines=[]
        self.leftAxisPoints=[]
        self.leftAxisParameters=[]
        self.rightAxisLines=[]
        self.rightAxisPoints=[]
        self.rightAxisParameters=[]

    def add_data_line(self, data_line, dict_type, color, replace=False):
        super(CompositeDataWrapper, self).add_data_line(data_line,
                                                        dict_type,
                                                        replace = replace)
        self.lineColors[dict_type] = colors.to_hex(color)

    def delete_data_line(self, dict_type):
        super(CompositeDataWrapper, self).delete_data_line(dict_type)
        self.lineColors.pop(dict_type)

    def add_data_points(self, data_points, dict_type, color, join=False):
        super(CompositeDataWrapper, self).add_data_points(data_points,
                                                        dict_type,
                                                        join = join)
        self.pointColors[dict_type] = colors.to_hex(color)

    def delete_data_points(self, dict_type):
        super(CompositeDataWrapper, self).delete_data_points(dict_type)
        self.pointColors.pop(dict_type)

    def add_parameter(self, parameter, dict_type, color, replace=False):
        super(CompositeDataWrapper, self).add_parameter(parameter,
                                                        dict_type,
                                                        replace = replace)
        self.parameterColors[dict_type] = colors.to_hex(color)

    def delete_parameter(self, dict_type):
        super(CompositeDataWrapper, self).delete_parameter(dict_type)
        self.parameterColors.pop(dict_type)

class QtSigmanWindow(QW.QMainWindow):
    """Klasa zawierająca główne okno programu."""
    def __init__(self):
        QW.QMainWindow.__init__(self)
        self.setAttribute(QC.Qt.WA_DeleteOnClose)
        self.setWindowTitle("QtSigman")

        # Inicjalizacja biblioteki sigman i utworzenie pustego
        # CompositeDataWrapper
        compositeDataWrapper = CompositeDataWrapper()

        # Ustawienie elementów okna
        self.mainWidget = QW.QWidget(self)
        mainLayout = QW.QHBoxLayout(self.mainWidget)
        self.setCentralWidget(self.mainWidget)
        # Po lewej
        self.mplPlotWidget = mplWidgets.PlotWidget()
        mainLayout.addWidget(self.mplPlotWidget)
        # Po prawej
        rightVBoxLayout = QW.QVBoxLayout()
        
        lineListLabel = QW.QLabel()
        lineListLabel.setText("Dane ciągłe")
        lineList = QW.QListWidget()
        lineList.setSizePolicy(QW.QSizePolicy.Fixed,
                               QW.QSizePolicy.Expanding)
        rightVBoxLayout.addWidget(lineListLabel)
        rightVBoxLayout.addWidget(lineList)
        pointListLabel = QW.QLabel()
        pointListLabel.setText("Dane punktowe") 
        pointList = QW.QListWidget()
        pointList.setSizePolicy(QW.QSizePolicy.Fixed,
                                QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(pointListLabel)
        rightVBoxLayout.addWidget(pointList)
        parameterListLabel = QW.QLabel() 
        parameterListLabel.setText("Obliczone parametry")
        parameterList = QW.QListWidget()
        parameterList.setSizePolicy(QW.QSizePolicy.Fixed,
                                    QW.QSizePolicy.Expanding) 
        rightVBoxLayout.addWidget(parameterListLabel)
        rightVBoxLayout.addWidget(parameterList)
        mainLayout.addLayout(rightVBoxLayout)

        # Ustawienie paska menu
        self.file_menu = QW.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QC.Qt.CTRL + QC.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QW.QMenu('&Help', self)
        self.help_menu.addAction('&About', self.about)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)


    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QW.QMessageBox.about(self, "About",
                                    """QtSigman
Program zapewniający GUI do bezpośredniej obsługi biblioteki sigman do 
analizy danych.""")

        


def initialize():
    """Uruchamia aplikację."""
    app = QW.QApplication([])
    qtSigmanWindow = QtSigmanWindow()

        # TEST STUFF
    from sigman import file_manager as fm
    from sigman import analyzer
    bp_line = fm.import_line('example_data/BP.dat', line_type = 'bp')
    ecg_line = fm.import_line('example_data/EKG.dat', line_type = 'ecg')
    r_points = fm.import_points('example_data/R.dat', point_type = 'r') 
    data_lines={'bp':bp_line, 'ecg':ecg_line}
    data_points={'r':r_points}
    complete_data = CompositeDataWrapper(data_lines = data_lines, data_points = data_points)
    complete_data.leftAxisLines=['bp']
    complete_data.rightAxisLines=['ecg']
    complete_data.rightAxisPoints=['r']
    complete_data.leftAxisParameters=['hr']
    calculate_hr = analyzer.import_procedure('param_heart_rate')
    param_tuples = []
    for i in range(10,100,10):
        param_tuples.append((i-10,i))
    hr = analyzer.calculate_parameter(complete_data, param_tuples ,calculate_hr,
                                  calculate_hr.default_settings, 'hr')
    complete_data.add_parameter(hr, 'hr', 'C2')
    beginTime, endTime = complete_data.calculate_complete_time_span()
    qtSigmanWindow.mplPlotWidget.plotCanvas.plotCompositeDataWrapper(complete_data,
                                                           beginTime,
                                                           endTime)
        # END OF TEST STUFF

    qtSigmanWindow.show()
    app.exec()
