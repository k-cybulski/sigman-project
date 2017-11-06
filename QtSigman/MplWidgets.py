"""
Moduł zajmujący się widgetem wizualizującym wykres.
"""
from enum import Enum, auto

from PyQt5 import QtWidgets as QW
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import sigman as sm

class Axis(Enum):
    Left = auto()
    Right = auto()
    Hidden = auto()

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        figure = matplotlib.figure.Figure()
        figure.set_tight_layout(True)

        super(PlotCanvas, self).__init__(figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QW.QSizePolicy.Expanding,
                                   QW.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        
    def plotCompositeDataWrapper(self, compositeDataWrapper, beginTime, endTime):
        self.figure.clf()
        self.axisLeft = self.figure.add_subplot(1,1,1)
        self.axisRight = self.axisLeft.twinx()
        
        for dataDict in compositeDataWrapper.dataDicts:
            for key, data in dataDict.items():
                axis = data.axis
                if axis is Axis.Hidden:
                    continue
                elif axis is Axis.Left:
                    plot_axis = self.axisLeft
                elif axis is Axis.Right:
                    plot_axis = self.axisRight
                data.plot(plot_axis, beginTime, endTime)

        self.draw()

class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

class PlotWidget(QW.QWidget):
    def __init__(self, parent=None):     
        super(PlotWidget, self).__init__(parent)

        self.plotCanvas = PlotCanvas()
        self.plotNavigationToolbar = NavigationToolbar(self.plotCanvas, self)

        layout = QW.QVBoxLayout(self)
        layout.addWidget(self.plotCanvas)
        layout.addWidget(self.plotNavigationToolbar)

    def updateCompositeData(self, compositeDataWrapper):
        #TODO: Wykres powinien być tylko odświeżony nie resetując pozycji
        # obserwatora
        beginTime, endTime = compositeDataWrapper.calculate_complete_time_span()
        self.plotCanvas.plotCompositeDataWrapper(compositeDataWrapper,
                                                 beginTime, endTime)
