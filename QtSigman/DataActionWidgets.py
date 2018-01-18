from enum import Enum
import glob
import re

from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QMessageBox as QMsgBox
from matplotlib import colors
from sigman import analyzer

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

        self.setWindowTitle(title)
        gridLayout = QW.QGridLayout()
        self.setLayout(gridLayout)

        self.typeLabel = QW.QLabel("Nazwa:")
        gridLayout.addWidget(self.typeLabel,1,1)
        self.typeLineEdit = QW.QLineEdit(dictType)
        self.typeLineEdit.selectAll()
        self.typeLineEdit.editingFinished.connect(self._setColorAccordingToDefault)
        gridLayout.addWidget(self.typeLineEdit,1,2)

        self.colorLabel = QW.QLabel("Kolor:")
        gridLayout.addWidget(self.colorLabel,2,1)
        self.colorLineEdit = QW.QLineEdit(color)
        self.colorLineEdit.editingFinished.connect(lambda:
            self.colorLineEdit.setText(
                _getColorString(self.colorLineEdit.text())))
        gridLayout.addWidget(self.colorLineEdit,2,2)
        self.colorPushButton = QW.QPushButton("Wybierz")
        self.colorPushButton.clicked.connect(lambda:
            self.colorLineEdit.setText(QW.QColorDialog.getColor().name()))
        gridLayout.addWidget(self.colorPushButton,2,3)

        self.axisLabel = QW.QLabel("Oś:")
        gridLayout.addWidget(self.axisLabel,3,1)
        self.axisComboBox = QW.QComboBox()
        axisItems = list(map(str, range(-1,2))) # Bardzo niechlujny hack ustawiający opcje w kolejności
        axisItems.remove(str(axis))
        axisItems.insert(0, str(axis))
        for i in range(len(axisItems)):
            if axisItems[i] == "-1":
                axisItems[i] = "-1 - Ukryta"
            elif axisItems[i] == "0":
                axisItems[i] = "0 - Lewa"
            elif axisItems[i] == "1":
                axisItems[i] = "1 - Prawa"
        self.axisComboBox.addItems(axisItems)
        gridLayout.addWidget(self.axisComboBox,3,2)

        self.offset = offset
        # offset jest None w wypadku parametrów, gdyż bezsensowe jest
        # przesuwanie ich w czasie
        if offset is not None:
            self.offsetLabel = QW.QLabel("Przesunięcie:")
            gridLayout.addWidget(self.offsetLabel,4,1)
            self.offsetLineEdit = QW.QLineEdit(offset)
            gridLayout.addWidget(self.offsetLineEdit,4,2)

        self.askDelete = askDelete
        if askDelete:
            self.deleteButton = QW.QPushButton("Usuń")
            self.deleteButton.clicked.connect(self.delete)
            gridLayout.addWidget(self.deleteButton,5,1)
        self.confirmButton = QW.QPushButton("Potwierdź")
        self.confirmButton.setDefault(True)
        self.confirmButton.clicked.connect(self.confirm)
        gridLayout.addWidget(self.confirmButton,5,2)

        self.rejectButton = QW.QPushButton("Anuluj")
        self.rejectButton.clicked.connect(self.reject)
        gridLayout.addWidget(self.rejectButton,5,3)

    def delete(self):
        reply = QW.QMessageBox.question(
            self, 'Potwierdzenie', "Czy na pewno usunąć?", 
            QW.QMessageBox.Yes | QW.QMessageBox.No, QW.QMessageBox.No)
        if reply == QW.QMessageBox.Yes:
            self.dataActionStatus = DataActionStatus.Delete
            self.accept()
    
    def confirm(self):
        if self.checkCorrectness():
            self.accept()

    def checkCorrectness(self):
        if self.typeLineEdit.text()=="":
            QW.QMessageBox.warning(self, "Błąd", "Nazwa nie może być pusta.")
            return False
        if self.typeLineEdit.text().strip() in self.forbiddenNames:
            QW.QMessageBox.warning(self, "Błąd", "Nazwa zajęta.")
            return False
        if _getColorString(self.colorLineEdit.text()) == "":
            QW.QMessageBox.warning(self, "Błąd", "Niewłaściwy kolor.")
            return False
        if self.offset is not None:
            try:
                float(self.offsetLineEdit.text())
            except ValueError:
                QW.QMessageBox.warning(
                    self, "Błąd", "Niewłaściwe przesunięcie (musi być liczbą)")
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
        """Pokazuje użytkownikowi okno wyboru ustawień danych,
        np. kolor czy nazwa, a następnie zwraca je w kolejności:
            nazwa (type), kolor, oś, status okna (anulowane/zaakceptowane
            /sugerujące usunięcie danych)"""
        dataSettingsWidget = cls(**kwargs)
        if not dataSettingsWidget.exec_():
            dataSettingsWidget.dataActionStatus = DataActionStatus.Cancel
        values = list(dataSettingsWidget.getValues())
        values.append(dataSettingsWidget.dataActionStatus)
        return tuple(values)

class ProcedureArgumentsWidget(QW.QWidget):
    """Widget zawierający pola tekstowe i przyciski informujące o 
    wszystkich argumentach danej procedury"""

    def _makeArgumentInformationWindow(self, key, item):
        """Generuje lambdę przywolującą okno o tytule i tekście.
        Wymagane do __init__, bo lambda w pętli for nie działa dobrze.
        """
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
    """Widget służący do wybierania przebiegów/punktów. Zawiera QLabel
    informujący o typie wymaganych danych a także QComboBox z możliwymi
    do wyboru.
    """
    def __init__(self, argumentType, options, parent=None):
        """Inicjalizuje DataArgumentWidget.

        argumentType -- string określający typ danych, np. 'ecg'
        options -- lista zawierające możliwe dane do wyboru
        """
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
    """Widget zawierający zestaw DataArgumentWidget. Służy do
    generowania dict argumentów waves oraz points dla procedur.
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
    """Widget zawierający wszystkie informacje i ustawienia dotyczące
    pojedynczej procedury.
    """
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
        
        if procedure.procedure_type == 'modify':
            requiredWaves = ["Przebieg"]
            requiredPoints = []
        else:
            requiredWaves = procedure.required_waves
            requiredPoints = procedure.required_points

        self.waveArgumentWidgets = {}
        self.pointArgumentWidgets = {}

        if len(requiredWaves) > 0:
            requiredWavesLabel = QW.QLabel("Wymagane przebiegi:")
            self.vBoxLayout.addWidget(requiredWavesLabel)
            self.requiredWavesWidget = DataArgumentCollectionWidget(
                requiredWaves, self.compositeDataWrapper.waves.keys())
            self.vBoxLayout.addWidget(self.requiredWavesWidget)
        
        if len(requiredPoints) > 0:
            requiredPointsLabel = QW.QLabel("Wymagane punkty:")
            self.vBoxLayout.addWidget(requiredPointsLabel)
            self.requiredPointsWidget = DataArgumentCollectionWidget(
                requiredPoints, self.compositeDataWrapper.points.keys())
            self.vBoxLayout.addWidget(self.requiredPointsWidget)

        timeRangeLayout = QW.QHBoxLayout()
        timeRangeLabel = QW.QLabel("Zakres czasowy:")
        timeRangeLayout.addWidget(timeRangeLabel)
        self.timeRangeLineEdit = QW.QLineEdit() 
        self._setMaximumTimeRange()
        timeRangeLayout.addWidget(self.timeRangeLineEdit)
        timeRangeMaximumButton = QW.QPushButton("Maksymalny zakres")
        timeRangeMaximumButton.clicked.connect(lambda:
            self._setMaximumTimeRange())
        timeRangeLayout.addWidget(timeRangeMaximumButton)
        timeRangeInfoButton = QW.QPushButton("?")
        timeRangeInfoText = ("Zakres czasu, na którym chcesz przeprowadzić "
                             "procedurę w formacie dwóch liczb przedzielonych "
                             "przecinkiem. Przycisk 'Maksymalny zakres' "
                             "oblicza największy możliwy zakres dla danych.")
        timeRangeInfoButton.clicked.connect(lambda:
            QW.QMessageBox.information(self, "Zakres czasowy",
                                       timeRangeInfoText))
        timeRangeLayout.addWidget(timeRangeInfoButton)
        self.vBoxLayout.addLayout(timeRangeLayout)

        self.procedureArgumentsWidget = ProcedureArgumentsWidget(procedure)
        self.vBoxLayout.addWidget(self.procedureArgumentsWidget)

        bottomHBoxLayout = QW.QHBoxLayout()
        self.confirmButton = QW.QPushButton("Użyj")
        bottomHBoxLayout.addWidget(self.confirmButton)
        self.rejectButton = QW.QPushButton("Anuluj")
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
            # jeśli wymagane są tylko punkty nie jesteśmy w stanie
            # określić zakresu czasu
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
                QW.QMessageBox.warning(self, "Błąd ogólny",
                                       "Niewłaściwy zakres czasowy")
                return False
        except:
            QW.QMessageBox.warning(self, "Błąd ogólny",
                                   "Niewłaściwy zakres czasowy")
            return False
        if self.procedure.procedure_type == "modify":
            if not self.getSelectedWaves():
                QW.QMessageBox.warning(self, "Błąd ogólny",
                                   "Wybierz przebieg")
                return False
        else:
            #TODO: Sprawdzanie czy odpowiednie dane są dostępne na tym zakresie
            if self.procedure.required_waves and not self.getSelectedWaves():
                QW.QMessageBox.warning(self, "Błąd ogólny",
                    "Nie ma wszystkich wymaganych przebiegów")
                return False
            if self.procedure.required_points and not self.getSelectedPoints():
                QW.QMessageBox.warning(self, "Błąd ogólny",
                    "Nie ma wszystkich wymaganych punktów")
                return False
        arguments = self.procedureArgumentsWidget.getArguments()
        if self.procedure.procedure_type == 'modify':
            wave = self.getSelectedWaves()['Przebieg']
            valid, message = self.procedure.validate_arguments(
                wave, arguments)
        else:
            waves = self.getSelectedWaves()
            points = self.getSelectedPoints()
            valid, message = self.procedure.validate_arguments(
                waves, points, arguments)
        if not valid:
            QW.QMessageBox.warning(self, "Błąd argumentów",
                                   message)
            return False
        return True

    def getSelectedWaveKeys(self):
        """Zwraca dict kluczy w Composite_data.waves wybranych 
        przebiegów. Jeśli nie zostały wybrane, zwraca None.
        """
        try:
            waves = self.requiredWavesWidget.getArguments()
        except AttributeError:
            return None
        if not all(wave for wave in waves.values()):
            return None
        return waves

    def getSelectedWaves(self):
        """Zwraca dict wybranych przebiegów. Jeśli nie zostały wybrane,
        zwraca None.
        """
        waves = self.getSelectedWaveKeys()
        if (not waves
            or not all(wave for wave in waves.values())):
            return None
        for key, item in waves.items():
            waves[key] = self.compositeDataWrapper.waves[item]
        return waves

    def getSelectedPointsKeys(self):
        """Zwraca dict kluczy w Composite_data.points wybranych punktów. 
        Jeśli nie zostały wybrane, zwraca None.
        """
        try:
            points = self.requiredPointsWidget.getArguments()
        except AttributeError:
            return None
        if not all(point for point in points.values()):
            return None
        return points

    def getSelectedPoints(self):
        """Zwraca dict wybranych punktów. Jeśli nie zostały wybrane,
        zwraca None.
        """
        points = self.getSelectedPointsKeys()
        if (not points
            or not all(point for point in points.values())):
            return None
        for key, item in points.items():
            points[key] = self.compositeDataWrapper.points[item]
        return points

class ProcedureDialog(QW.QDialog):
    """Okno dialogowe wyświetlające listę dostępnych procedur danego
    typu oraz informacje o nich i ich ustawienia.

    Wszystkie procedury importuje w momencie uruchomienia.
    """

    def __init__(self, procedureType, compositeDataWrapper, parent=None):
        super().__init__(parent)

        self.dataActionStatus = DataActionStatus.Ok

        # Generujemy listę wszystkich procedur
        self.procedureType = procedureType
        procedureFilter = "procedures/"+procedureType+"_*"
        self.procedureFiles = glob.glob(procedureFilter)
        cutoutLength = len(procedureFilter)-1
        self.procedureNames = [proc[cutoutLength:-3] for
            proc in self.procedureFiles]
        self.procedures = []
        for proc in self.procedureNames:
            self.procedures.append(
                analyzer.import_procedure(self.getModuleName(proc)))
        if len(self.procedures) == 0:
            QW.QMessageBox.warning(self, "Błąd",
                                   "Nie wykryto procedur")
            return

        # Ustawiamy layout
        mainHBoxLayout =  QW.QHBoxLayout()
        self.setLayout(mainHBoxLayout)

        # Ustawiamy listę procedur i stawiamy po lewej
        self.listWidget = QW.QListWidget(self)
        for proc in self.procedureNames:
            item = QW.QListWidgetItem(self.listWidget)
            item.setText(proc)
            self.listWidget.addItem(item)
        mainHBoxLayout.addWidget(self.listWidget)

        # Szykujemy QStackedWidget wypełniony ProcedureWidget i 
        # stawiamy po prawej
        self.stackedWidget = QW.QStackedWidget(self)
        self.procedureWidgetDict = {}
        for proc, procName in zip(self.procedures, self.procedureNames):
            procedureWidget = ProcedureWidget(proc, compositeDataWrapper)
            self.procedureWidgetDict[procName] = procedureWidget
            self.stackedWidget.addWidget(procedureWidget)
            procedureWidget.confirmButton.clicked.connect(self.confirm)
            procedureWidget.rejectButton.clicked.connect(self.reject)
        mainHBoxLayout.addWidget(self.stackedWidget)

        # Implementujemy wybieranie procedur
        self.selectedProcedureName = self.procedureNames[0]
        self.listWidget.itemClicked.connect(lambda itemWidget:
            self.selectProcedure(itemWidget.text()))

    def selectProcedure(self, procedureName):
        if procedureName in self.procedureNames:
            self.selectedProcedureName = procedureName
            self.stackedWidget.setCurrentWidget(
                self.procedureWidgetDict[procedureName])
        else:
            raise ValueError("Nie ma takiej procedury")

    def getModuleName(self, procedure):
        """Zwraca nazwę modułu kompatybilną z analyzer.import_module."""
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
                wave = selectedProcedureWidget.getSelectedWaveKeys()['Przebieg']
                beginTime, endTime = selectedProcedureWidget.getTimeRange()
                procedure = selectedProcedureWidget.procedure
                arguments = selectedProcedureWidget.getArguments()
                return wave, beginTime, endTime, procedure, arguments
            else:
                return None, None, None, None, None
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
