from enum import Enum
import glob
import re

from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QMessageBox as QMsgBox
from matplotlib import colors
from sigman import analyzer
from sigman.analyzer import InvalidArgumentError

from QtSigman.DefaultColors import defaultColors

def _getColorString(inputColor):
    try:
        out = colors.to_hex(inputColor)
    except:
        return ""
    return out

class DataActionStatus(Enum):
    Ok = 1
    Cancel = 2
    Delete = 3

class DataSettingsDialog(QW.QDialog):
    def __init__(self, title="", dictType="default", color="#1f77b4", 
                 forbiddenNames=[], parent=None, axis=-1,
                 offset='0', askDelete=False):
        super(DataSettingsDialog, self).__init__(parent = parent)
        
        self.forbiddenNames = forbiddenNames
        self.dataActionStatus = DataActionStatus.Ok
        if (isinstance (title, str)):
            self.setWindowTitle(title)
        else:
            self.setWindowTitle(title[0])
        gridLayout = QW.QGridLayout()
        self.setLayout(gridLayout)

        self.typeLabel = QW.QLabel("Type:")
        gridLayout.addWidget(self.typeLabel,1,1)
        self.typeLineEdit = QW.QLineEdit(dictType)
        self.typeLineEdit.selectAll()
        self.typeLineEdit.editingFinished.connect(self._setColorAccordingToDefault)
        gridLayout.addWidget(self.typeLineEdit,1,2)

        self.colorLabel = QW.QLabel("Colour:")
        gridLayout.addWidget(self.colorLabel,2,1)
        self.colorLineEdit = QW.QLineEdit(color)
        self.colorLineEdit.editingFinished.connect(lambda:
            self.colorLineEdit.setText(
                _getColorString(self.colorLineEdit.text())))
        gridLayout.addWidget(self.colorLineEdit,2,2)
        self.colorPushButton = QW.QPushButton("Choose")
        self.colorPushButton.clicked.connect(lambda:
            self.colorLineEdit.setText(QW.QColorDialog.getColor().name()))
        gridLayout.addWidget(self.colorPushButton,2,3)

        self.axisLabel = QW.QLabel("Axis:")
        gridLayout.addWidget(self.axisLabel,3,1)
        self.axisComboBox = QW.QComboBox()
        axisItems = list(map(str, range(-1,2))) # Nasty hack to sort these
        axisItems.remove(str(axis))
        axisItems.insert(0, str(axis))
        for i in range(len(axisItems)):
            if axisItems[i] == "-1":
                axisItems[i] = "-1 - Hidden"
            elif axisItems[i] == "0":
                axisItems[i] = "0 - Left"
            elif axisItems[i] == "1":
                axisItems[i] = "1 - Right"
        self.axisComboBox.addItems(axisItems)
        gridLayout.addWidget(self.axisComboBox,3,2)

        self.offset = offset
        # offset is none when considering `Parameter` objects
        if offset is not None:
            self.offsetLabel = QW.QLabel("Offset:")
            gridLayout.addWidget(self.offsetLabel,4,1)
            self.offsetLineEdit = QW.QLineEdit(offset)
            gridLayout.addWidget(self.offsetLineEdit,4,2)

        self.askDelete = askDelete
        if askDelete:
            self.deleteButton = QW.QPushButton("Delete")
            self.deleteButton.clicked.connect(self.delete)
            gridLayout.addWidget(self.deleteButton,5,1)
        self.confirmButton = QW.QPushButton("Confirm")
        self.confirmButton.setDefault(True)
        self.confirmButton.clicked.connect(self.confirm)
        gridLayout.addWidget(self.confirmButton,5,2)

        self.rejectButton = QW.QPushButton("Cancel")
        self.rejectButton.clicked.connect(self.reject)
        gridLayout.addWidget(self.rejectButton,5,3)

    def delete(self):
        reply = QW.QMessageBox.question(
            self, 'Confirmation', "Are you sure you wish to delete it?", 
            QW.QMessageBox.Yes | QW.QMessageBox.No, QW.QMessageBox.No)
        if reply == QW.QMessageBox.Yes:
            self.dataActionStatus = DataActionStatus.Delete
            self.accept()
    
    def confirm(self):
        if self.checkCorrectness():
            self.accept()

    def checkCorrectness(self):
        if self.typeLineEdit.text()=="":
            QW.QMessageBox.warning(self, "Error", "Type may not be empty.")
            return False
        if self.typeLineEdit.text().strip() in self.forbiddenNames:
            QW.QMessageBox.warning(self, "Error", "Type taken.")
            return False
        if _getColorString(self.colorLineEdit.text()) == "":
            QW.QMessageBox.warning(self, "Error", "Invalid colour.")
            return False
        if self.offset is not None:
            try:
                float(self.offsetLineEdit.text())
            except ValueError:
                QW.QMessageBox.warning(
                    self, "Error", "Invalid offset (must be a number of seconds)")
                return False
        return True

    def getValues(self):
        if self.dataActionStatus is DataActionStatus.Ok:
            dictType = self.typeLineEdit.text().strip()
            color = self.colorLineEdit.text()
            axis = int(re.findall("^[-0-9][0-9]*", 
                                  self.axisComboBox.currentText())[0])
            if self.offset is not None:
                offset = float(self.offsetLineEdit.text())
                return dictType, color, axis, offset
            return dictType, color, axis
        else:
            if self.offset is not None:
                return None, None, None, None
            return None, None, None

    def _setColorAccordingToDefault(self):
        key = self.typeLineEdit.text()
        if key in defaultColors:
            self.colorLineEdit.setText(defaultColors[key])

    @classmethod
    def getDataSettings(cls, **kwargs):
        """Shows the user a dialog box with data settings, e.g.
        type or colour, and returns them as a tuple:
            type, colour, axis, status (cancelled/accepted/asking for
            data removal)
        """
        dataSettingsWidget = cls(**kwargs)
        if not dataSettingsWidget.exec_():
            dataSettingsWidget.dataActionStatus = DataActionStatus.Cancel
        values = list(dataSettingsWidget.getValues())
        values.append(dataSettingsWidget.dataActionStatus)
        return tuple(values)

class ProcedureArgumentsWidget(QW.QWidget):
    """Widget containing text fields and buttons pertaining to all 
    arguments of a given procedure."""

    def _makeArgumentInformationWindow(self, key, item):
        """Generates an information dialog box showing function."""
        return lambda: QW.QMessageBox.information(self, key, item)

    def __init__(self, procedure, parent=None):
        super().__init__(parent)

        gridLayout = QW.QGridLayout()
        self.setLayout(gridLayout)

        self.argumentLineEdits = {}
        pos = 0
        for key, item in procedure.arguments.items():
            argumentNameLabel = QW.QLabel(key)
            argumentLineEdit = QW.QLineEdit()
            argumentLineEdit.setText(str(procedure.default_arguments[key]))
            self.argumentLineEdits[key] = argumentLineEdit
            argumentInfoButton = QW.QPushButton("?")
            argumentInfoButton.clicked.connect(
                self._makeArgumentInformationWindow(key, item))
            gridLayout.addWidget(argumentNameLabel, pos, 0)
            gridLayout.addWidget(argumentLineEdit, pos, 1)
            gridLayout.addWidget(argumentInfoButton, pos, 2)
            pos += 1

    def getArguments(self):
        arguments = {}
        for key, item in self.argumentLineEdits.items():
            arguments[key] = item.text()
        return arguments

class DataArgumentWidget(QW.QWidget):
    """Widget used for choosing `Wave`/`Points` arguments"""

    def __init__(self, argumentType, options, parent=None):
        super().__init__(parent)

        hBoxLayout = QW.QHBoxLayout()
        hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hBoxLayout)

        self.argumentType = argumentType

        # no need to keep in .self
        self.argumentTypeWidget = QW.QLabel(argumentType+":")
        hBoxLayout.addWidget(self.argumentTypeWidget)

        self.optionComboBox = QW.QComboBox() 
        self.optionComboBox.addItems(options)
        hBoxLayout.addWidget(self.optionComboBox)

    def getSelectedOption(self):
        return self.optionComboBox.currentText()

class DataArgumentCollectionWidget(QW.QWidget):
    """Widget containing a list of `DataArgumentWidget` instances
    used for generating data argument dicts.
    """
    def __init__(self, wantedArguments, options, parent=None):
        super().__init__(parent)

        gridLayout = QW.QGridLayout()
        gridLayout.setSpacing(0)
        gridLayout.setContentsMargins(0,0,0,0)
        self.setLayout(gridLayout)

        self.argumentWidgets = []
        for arg in wantedArguments:
            argWidget = DataArgumentWidget(arg, options, self)
            self.argumentWidgets.append(argWidget)
            gridLayout.addWidget(argWidget,len(self.argumentWidgets),1)

    def getArguments(self):
        arguments = {}
        for argWidget in self.argumentWidgets:
            arguments[argWidget.argumentType] = argWidget.getSelectedOption()
        return arguments

class ProcedureWidget(QW.QWidget):
    def __init__(self, procedure, compositeDataWrapper, parent=None):
        super().__init__(parent)
        
        self.procedure = procedure
        self.compositeDataWrapper = compositeDataWrapper

        self.vBoxLayout = QW.QVBoxLayout()
        self.setLayout(self.vBoxLayout)

        self.nameWidget = QW.QLabel(procedure.__name__)
        self.vBoxLayout.addWidget(self.nameWidget)

        self.descriptionWidget = QW.QTextEdit()
        self.descriptionWidget.setReadOnly(True)
        self.descriptionWidget.setText(procedure.description)
        self.descriptionWidget.setMinimumWidth(480)
        self.vBoxLayout.addWidget(self.descriptionWidget)
        
        # modify procedures only have a single wave input
        if procedure.procedure_type == 'modify':
            requiredWaves = ["Waveform"]
            requiredPoints = []
        elif hasattr(procedure, 'required_waves'):
            requiredWaves = procedure.required_waves        
        else:
            requiredWaves = []

        if hasattr(procedure, 'required_points'):
            requiredPoints = procedure.required_points
        else:
            requiredPoints = []

        self.waveArgumentWidgets = {}
        self.pointArgumentWidgets = {}

        if len(requiredWaves) > 0:
            requiredWavesLabel = QW.QLabel("Required waveforms:")
            self.vBoxLayout.addWidget(requiredWavesLabel)
            self.requiredWavesWidget = DataArgumentCollectionWidget(
                requiredWaves, self.compositeDataWrapper.waves.keys())
            self.vBoxLayout.addWidget(self.requiredWavesWidget)
        
        if len(requiredPoints) > 0:
            requiredPointsLabel = QW.QLabel("Required points:")
            self.vBoxLayout.addWidget(requiredPointsLabel)
            self.requiredPointsWidget = DataArgumentCollectionWidget(
                requiredPoints, self.compositeDataWrapper.points.keys())
            self.vBoxLayout.addWidget(self.requiredPointsWidget)

        timeRangeLayout = QW.QHBoxLayout()
        timeRangeLabel = QW.QLabel("Time range:")
        timeRangeLayout.addWidget(timeRangeLabel)
        self.timeRangeLineEdit = QW.QLineEdit() 
        self._setMaximumTimeRange()
        timeRangeLayout.addWidget(self.timeRangeLineEdit)
        timeRangeMaximumButton = QW.QPushButton("Maximum time range")
        timeRangeMaximumButton.clicked.connect(lambda:
            self._setMaximumTimeRange())
        timeRangeLayout.addWidget(timeRangeMaximumButton)
        timeRangeInfoButton = QW.QPushButton("?")
        timeRangeInfoText = ("Time range in which you wish to execute the "
                             "procedure in the form of two numbers split by "
                             "a comma.")
        timeRangeInfoButton.clicked.connect(lambda:
            QW.QMessageBox.information(self, "Time range",
                                       timeRangeInfoText))
        timeRangeLayout.addWidget(timeRangeInfoButton)
        self.vBoxLayout.addLayout(timeRangeLayout)

        self.procedureArgumentsWidget = ProcedureArgumentsWidget(procedure)
        self.vBoxLayout.addWidget(self.procedureArgumentsWidget)

        bottomHBoxLayout = QW.QHBoxLayout()
        self.confirmButton = QW.QPushButton("Confirm")
        bottomHBoxLayout.addWidget(self.confirmButton)
        self.rejectButton = QW.QPushButton("Cancel")
        bottomHBoxLayout.addWidget(self.rejectButton)
        self.vBoxLayout.addLayout(bottomHBoxLayout)

    def _setMaximumTimeRange(self):
        if ((self.procedure.procedure_type == 'modify' 
                or len(self.procedure.required_waves) > 0)
                and self.getSelectedWaves()):
            waves = self.requiredWavesWidget.getArguments().values()
            begin, end = self.compositeDataWrapper.calculate_time_range(waves)
            text = str(begin) + ", " + str(end)
            self.timeRangeLineEdit.setText(text)
        else:
            # if only points are required for the procedure we are not able to
            # determine the maximum time range
            pass

    def getTimeRange(self):
        vals = self.timeRangeLineEdit.text().strip().split(',')
        outputValues = []
        for val in vals:
            outputValues.append(float(val))
        return outputValues

    def getArguments(self):
        return self.procedureArgumentsWidget.getArguments()

    def checkCorrectness(self):
        try:
            vals = self.timeRangeLineEdit.text().strip().split(',')
            for val in vals:
                float(val)
            if len(vals) != 2:
                QW.QMessageBox.warning(self, "Error",
                                       "Invalid time range")
                return False
        except:
            QW.QMessageBox.warning(self, "Error",
                                   "Invalid time range")
            return False
        if self.procedure.procedure_type == "modify":
            if not self.getSelectedWaves():
                QW.QMessageBox.warning(self, "Error",
                                   "Choose a waveform")
                return False
        else:
            if self.procedure.required_waves and not self.getSelectedWaves():
                QW.QMessageBox.warning(self, "Error",
                    "Not all required waveforms given")
                return False
            if self.procedure.required_points and not self.getSelectedPoints():
                QW.QMessageBox.warning(self, "Error",
                    "Not all required points given")
                return False
        arguments = self.procedureArgumentsWidget.getArguments()
        if len(self.procedure.arguments) > 0:
            if self.procedure.procedure_type == 'modify':
                wave = self.getSelectedWaves()['Waveform']
                points = self.getSelectedPoints()
                try:
                    self.procedure.interpret_arguments(
                        wave, points, arguments)
                except InvalidArgumentError as e:
                    QW.QMessageBox.warning(self, "Invalid arguments",
                                           e.args[0])
                    return False

            else:
                waves = self.getSelectedWaves()
                points = self.getSelectedPoints()
                try:
                    self.procedure.interpret_arguments(
                        waves, points, arguments)
                except InvalidArgumentError as e:
                    QW.QMessageBox.warning(self, "Invalid arguments",
                                           e.args[0])
                    return False
        return True

    def getSelectedWaveKeys(self):
        """Returns a `dict` of `<required waveform>:<chosen waveform name>`
        pairs.

        If not chosen, returns None.
        """
        try:
            waves = self.requiredWavesWidget.getArguments()
        except AttributeError:
            return None
        if not all(wave for wave in waves.values()):
            return None
        return waves

    def getSelectedWaves(self):
        """Returns a `dict` of `<required waveform>:<chosen `Wave` instance>`
        pairs.

        If not chosen, returns None.
        """
        waves = self.getSelectedWaveKeys()
        if (not waves
            or not all(wave for wave in waves.values())):
            return None
        for key, item in waves.items():
            waves[key] = self.compositeDataWrapper.waves[item]
        return waves

    def getSelectedPointsKeys(self):
        """Returns a `dict` of `<required points>:<chosen points name>`
        pairs.

        If not chosen, returns None.
        """
        try:
            points = self.requiredPointsWidget.getArguments()
        except AttributeError:
            return None
        if not all(point for point in points.values()):
            return None
        return points

    def getSelectedPoints(self):
        """Returns a `dict` of `<required points>:<chosen `Points` instance>`
        pairs.

        If not chosen, returns None.
        """
        points = self.getSelectedPointsKeys()
        if (not points
            or not all(point for point in points.values())):
            return None
        for key, item in points.items():
            points[key] = self.compositeDataWrapper.points[item]
        return points

class ProcedureDialog(QW.QDialog):
    """Dialog window containing a list of available procedures of a
    given type as well as information about them and their settings.

    All procedures are imported at the moment it's initialized.
    """

    def __init__(self, procedureType, compositeDataWrapper, parent=None):
        super().__init__(parent)

        self.dataActionStatus = DataActionStatus.Ok

        # Generate a list of all procedures
        self.procedureType = procedureType
        typeFilter = procedureType+"_"
        self.procedures = analyzer.import_procedures(type_filter=typeFilter)
        self.procedureNames = [procedure.__name__.split(typeFilter)[-1] for procedure in
                               self.procedures]
        if len(self.procedures) == 0:
            QW.QMessageBox.warning(self, "Error",
                                   "Procedures not found in `procedures/` "
                                   "directory.")
            return

        # Set up the layout
        mainHBoxLayout =  QW.QHBoxLayout()
        self.setLayout(mainHBoxLayout)

        # Set up the list of procedures and put it on the left
        self.listWidget = QW.QListWidget(self)
        for proc in self.procedureNames:
            item = QW.QListWidgetItem(self.listWidget)
            item.setText(proc)
            self.listWidget.addItem(item)
        mainHBoxLayout.addWidget(self.listWidget)

        # Set up a QStackedWidget filled with ProcedureWidgets and put
        # it on the left
        self.stackedWidget = QW.QStackedWidget(self)
        self.procedureWidgetDict = {}
        for proc, procName in zip(self.procedures, self.procedureNames):
            procedureWidget = ProcedureWidget(proc, compositeDataWrapper)
            self.procedureWidgetDict[procName] = procedureWidget
            self.stackedWidget.addWidget(procedureWidget)
            procedureWidget.confirmButton.clicked.connect(self.confirm)
            procedureWidget.rejectButton.clicked.connect(self.reject)
        mainHBoxLayout.addWidget(self.stackedWidget)

        # Implement procedure choice
        self.selectedProcedureName = self.procedureNames[0]
        self.listWidget.itemClicked.connect(lambda itemWidget:
            self.selectProcedure(itemWidget.text()))

    def selectProcedure(self, procedureName):
        if procedureName in self.procedureNames:
            self.selectedProcedureName = procedureName
            self.stackedWidget.setCurrentWidget(
                self.procedureWidgetDict[procedureName])
        else:
            raise ValueError("No such procedure")

    def getModuleName(self, procedure):
        """Returns a module name compatible with analyzer.import_module."""
        return self.procedureType+"_"+procedure

    def confirm(self):
        if self.checkCorrectness():
            self.accept()

    def checkCorrectness(self):
        selectedProcedureWidget = self.procedureWidgetDict[self.selectedProcedureName]
        return selectedProcedureWidget.checkCorrectness()


    def getValues(self):
        if self.procedureType == 'modify':
            if self.dataActionStatus is DataActionStatus.Ok:
                selectedProcedureWidget = self.procedureWidgetDict[self.selectedProcedureName]
                wave = selectedProcedureWidget.getSelectedWaveKeys()['Waveform']
                beginTime, endTime = selectedProcedureWidget.getTimeRange()
                procedure = selectedProcedureWidget.procedure
                arguments = selectedProcedureWidget.getArguments()

                if hasattr(procedure, 'required_points'):
                    pointsDict = selectedProcedureWidget.getSelectedPoints()
                else:
                    pointsDict = []
                return wave, pointsDict, beginTime, endTime, procedure, arguments 
            else:
                return None, None, None, None, None, None
        else:
            if self.dataActionStatus is DataActionStatus.Ok:
                selectedProcedureWidget = self.procedureWidgetDict[self.selectedProcedureName]
                waveDict = selectedProcedureWidget.getSelectedWaves()
                pointsDict = selectedProcedureWidget.getSelectedPoints()
                beginTime, endTime = selectedProcedureWidget.getTimeRange()
                procedure = selectedProcedureWidget.procedure
                arguments = selectedProcedureWidget.getArguments()
                return waveDict, pointsDict, beginTime, endTime, procedure, arguments
            else:
                return None, None, None, None, None, None

    @classmethod
    def getProcedure(cls, procedureType, compositeDataWrapper):
        procedureWidget = cls(procedureType, compositeDataWrapper)
        if not procedureWidget.exec_():
            procedureWidget.dataActionStatus = DataActionStatus.Cancel
        values = list(procedureWidget.getValues())
        values.append(procedureWidget.dataActionStatus)
        return tuple(values)

class ModelflowImportDialog(QW.QDialog):
    """Dialog for importing modelflow data""" 
    
    def __init__(self, path,compositeDataWrapper):
        super().__init__()
        self.title = "Import data"
        self.setWindowTitle(self.title)
        gridLayout = QW.QGridLayout()
        self.setLayout(gridLayout)
       
        self.typeLabel = QW.QLabel("Path to modelflow data:")
        gridLayout.addWidget(self.typeLabel,1,1)

        self.pathLabel = QW.QLabel(path)
        gridLayout.addWidget(self.pathLabel,2,1)
        
        self.changeButton = QW.QPushButton("Change")
        self.changeButton.clicked.connect(self.Change)
        gridLayout.addWidget(self.changeButton,2,2)


        self.matchLabel = QW.QLabel("Choose the used type of points to match:")
        gridLayout.addWidget(self.matchLabel,3,1)

        self.matchList = QW.QComboBox()
        
        if '.A00' in path:
            axisItems = ['SBP','DBP','R']
        else:
            axisItems = ['R']
        self.matchList.addItems(axisItems)
        self.matchList.setCurrentIndex(0)
        gridLayout.addWidget(self.matchList,4,1)

        self.selectLabel = QW.QLabel("Choose points used to match the data:")
        gridLayout.addWidget(self.selectLabel,5,1)

        self.listPoints = QW.QComboBox()

        for name in compositeDataWrapper.points.keys():
            self.listPoints.addItem(name)
        self.listPoints.setCurrentIndex(0)
        gridLayout.addWidget(self.listPoints,6,1)

        self.confirmButton = QW.QPushButton("Confirm")
        self.confirmButton.setDefault(True)
        self.confirmButton.clicked.connect(self.Confirm)
        gridLayout.addWidget(self.confirmButton,7,2)

        self.abortButton = QW.QPushButton("Cancel")
        self.abortButton.clicked.connect(self.reject)
        gridLayout.addWidget(self.abortButton,7,1)
        self.setGeometry(300, 300, 290, 150)

        self.exec()
        self.show()

    def Confirm(self): 
        self.accept()
        return DataActionStatus.Ok 
        self.close()

    def PathModelflow(self):
        return self.pathLabel.text()

    def SelectedPointsType(self):
        return self.matchList.currentIndex()

    def SelectedPoints(self):
        return self.listPoints.currentText()

    def Change(self):
         fileFilter = ('all_supported_files (*.csv *.A00);; '
            'BeatScope (*.A00);; Finapres Nova (*.csv);; '
            'all_files (*)')

         fileDialog = QW.QFileDialog()
         fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
         newpath = fileDialog.getOpenFileName(filter = fileFilter)
         self.matchList.clear()
         if '.A00' in newpath:
            axisItems = ['SBP','DBP','R']
         else:
            axisItems = ['R']
         self.matchList.addItems(axisItems)
         self.pathLabel.setText(newpath[0])

