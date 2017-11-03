"""
Moduł zajmujący się rysownaniem wykresów.
"""
from PyQt5 import QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT
import sigman as sm

def plotDataLine(axis, dataLine, beginTime, endTime, color):
    x, y = dataLine.generate_coordinate_tables(
        begin_time = beginTime,
        end_time = endTime,
        begin_x = beginTime)
    axis.plot(x, y, color = color)

def plotDataPoints(axis, dataPoints, beginTime, endTime, color):
    x, y = dataPoints.data_slice(beginTime, endTime)
    axis.plot(x, y, color = color, marker = 'o', linestyle = 'None')

def plotParameter(axis, parameter, beginTime, endTime, color):
    lineTuples = parameter.generate_parameter_line_tuples(
        begin_time = beginTime, end_time = endTime)
    for tup in lineTuples:
        axis.plot(tup[0], tup[1], color = color)

def plotData(axis, data, beginTime, endTime, color):
    if isinstance(data, sm.Data_line):
        plotDataLine(axis, data, beginTime, endTime, color)
    if isinstance(data, sm.Data_points):
        plotDataPoints(axis, data, beginTime, endTime, color)
    if isinstance(data, sm.Parameter):
        plotParameter(axis, data, beginTime, endTime, color)


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        figure = matplotlib.figure.Figure()
        figure.set_tight_layout(True)

        super(PlotCanvas, self).__init__(figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        
    def plotCompositeDataWrapper(self, compositeDataWrapper, beginTime, endTime):
        self.figure.clf()
        self.axisLeft = self.figure.add_subplot(1,1,1)
        self.axisRight = self.axisLeft.twinx()
        for key in compositeDataWrapper.leftAxisLines:
            color = compositeDataWrapper.lineColors[key]
            data = compositeDataWrapper.data_lines[key]
            plotData(self.axisLeft, data, beginTime, endTime, color)
        for key in compositeDataWrapper.rightAxisLines:
            color = compositeDataWrapper.lineColors[key]
            data = compositeDataWrapper.data_lines[key]
            plotData(self.axisRight, data, beginTime, endTime, color)

        for key in compositeDataWrapper.leftAxisPoints:
            color = compositeDataWrapper.pointColors[key]
            data = compositeDataWrapper.data_points[key]
            plotData(self.axisLeft, data, beginTime, endTime, color)
        for key in compositeDataWrapper.rightAxisPoints:
            color = compositeDataWrapper.pointColors[key]
            data = compositeDataWrapper.data_points[key]
            plotData(self.axisRight, data, beginTime, endTime, color)

        for key in compositeDataWrapper.leftAxisParameters:
            color = compositeDataWrapper.parameterColors[key]
            data = compositeDataWrapper.parameters[key]
            plotData(self.axisLeft, data, beginTime, endTime, color)
        for key in compositeDataWrapper.rightAxisParameters:
            color = compositeDataWrapper.parameterColors[key]
            data = compositeDataWrapper.parameters[key]
            plotData(self.axisRight, data, beginTime, endTime, color)
        self.draw()

class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

class PlotWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):     
        super(PlotWidget, self).__init__(parent)

        self.plotCanvas = PlotCanvas()
        self.plotNavigationToolbar = NavigationToolbar(self.plotCanvas, self)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.plotCanvas)
        layout.addWidget(self.plotNavigationToolbar)
