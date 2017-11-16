"""
Moduł zajmujący się widgetem wizualizującym wykres.
"""
from enum import Enum

from PyQt5 import QtWidgets as QW
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import matplotlib.patches as mPatches
import sigman as sm

class Axis(Enum):
    Left = 1
    Right = 2
    Hidden = 3

class PlotCanvas(FigureCanvas):
    """Widget przedstawiający sam wykres."""
    
    def __init__(self, parent=None):
        figure = matplotlib.figure.Figure()
        figure.set_tight_layout(True)
        super(PlotCanvas, self).__init__(figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QW.QSizePolicy.Expanding,
                                   QW.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.axisLeft = self.figure.add_subplot(1,1,1)
        self.axisRight = self.axisLeft.twinx()

        
        
    def plotCompositeDataWrapper(self, compositeDataWrapper, beginTime, endTime):
        """Rysuje lub tylko odświeża już narysowane dane z 
        CompositeDataWrapper.
        """

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
            for plot_axis in [self.axisLeft, self.axisRight]:
                plot_axis.relim()
                plot_axis.autoscale(axis='y')
        self.draw()

    def plotDataWaveComparison(self, dataWaveDict, beginTime, endTime):
        """Rysuje VisualDataWave z dict oraz podpisuje je zgodnie z ich
        kluczem w dict.
        """
        # Chcemy listę defaultowych kolorów matplotlib
        prop_cycle = matplotlib.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']
        handles = []
        for key, item in dataWaveDict.items():
            color = colors.pop(0)
            colors.append(color)
            handles.append(
                mPatches.Patch(color = color, label = key))
            item.plot(self.axisLeft, beginTime, endTime, 
                      keepMplObject = False, color = color)
        self.axisLeft.legend(handles = handles)

class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Pan', 'Zoom', 'Save')] # 'Home' do skorygowania

class PlotWidget(QW.QWidget):
    """Widget przedstawiający wykres wraz z paskiem nawigacji."""

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


