from enum import Enum, auto
import glob

from PyQt5 import QtWidgets as QW
from PyQt5.QtWidgets import QMessageBox as QMsgBox
from matplotlib import colors
from sigman import analyzer

from QtSigman.MplWidgets import Axis
from QtSigman.DefaultColors import defaultColors

def _getColorString(inputColor):
    try:
        out = colors.to_hex(inputColor)
    except:
        return ""
    return out

class DataActionStatus(Enum):
    Ok = auto()
    Cancel = auto()
    Delete = auto()

class DataSettingsDialog(QW.QDialog):
    def __init__(self, title="", dictType="default", color="#1f77b4", 
                 forbiddenNames=[], parent=None, axis=Axis.Left, 
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
        axisItems = [] # Bardzo niechlujny hack ustawiający opcje w kolejności
        if axis == Axis.Left:
            axisItems = ['Lewa','Prawa','Żadna (Ukryj)']
        elif axis == Axis.Right:
            axisItems = ['Prawa','Lewa','Żadna (Ukryj)']
        else:
            axisItems = ['Żadna (Ukryj)','Lewa','Prawa']
        self.axisComboBox.addItems(axisItems)
        gridLayout.addWidget(self.axisComboBox,3,2)

        self.offset = offset
        # offset jest None w wypadku parametrów, gdyż bezsensowne jest
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
            #TODO: CHANGE ALL INTO QW.QMessageBox.warning(self, 'title',
            # 'stuff')





            msg = QW.QMessageBox()
            msg.setIcon(QW.QMessageBox.Warning)
            msg.setText("Nazwa nie może być pusta.")
            msg.exec_()
            return False
        if self.typeLineEdit.text().strip() in self.forbiddenNames:
            msg = QW.QMessageBox()
            msg.setIcon(QW.QMessageBox.Warning)
            msg.setText("Nazwa zajęta.")
            msg.exec_()
            return False
        if _getColorString(self.colorLineEdit.text()) == "":
            msg = QW.QMessageBox()
            msg.setIcon(QW.QMessageBox.Warning)
            msg.setText("Niewłaściwy kolor.")
            msg.exec_()
            return False
        if self.offset is not None:
            try:
                float(self.offsetLineEdit.text())
            except ValueError:
                msg = QW.QMessageBox()
                msg.setIcon(QW.QMessageBox.Warning)
                msg.setText("Niewłaściwe przesunięcie (musi być liczbą).")
                msg.exec_()
                return False
        return True

    def getValues(self):
        if self.dataActionStatus is DataActionStatus.Ok:
            dictType = self.typeLineEdit.text().strip()
            color = self.colorLineEdit.text()
            tempAxis = self.axisComboBox.currentText()
            if tempAxis == 'Lewa':
                axis = Axis.Left
            elif tempAxis == 'Prawa':
                axis = Axis.Right
            else:
                axis = Axis.Hidden
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

        if procedure.procedure_type == 'filter':
            pass
        else:
            self.addRequiredDataWidgets()
        
        timeRangeLayout = QW.QHBoxLayout()
        timeRangeLabel = QW.QLabel("Zakres czasowy:")
        timeRangeLayout.addWidget(timeRangeLabel)
        self.timeRangeLineEdit = QW.QLineEdit() 
        self._setMaximumTimeRange(initial=True)
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

    def _setMaximumTimeRange(self, initial=False):
        if not all(wave in self.compositeDataWrapper.data_waves for wave 
                   in self.procedure.required_waves):
            if initial:
                self.timeRangeLineEdit.setText('0,1')
                return
            QW.QMessageBox.warning(self, "Błąd ogólny",
                                   "Nie ma wszystkich wymaganych przebiegów")
            return
        beginTime, endTime = self.compositeDataWrapper.calculate_time_range(
            self.procedure.required_waves)
        timeRangeString = str(beginTime)+","+str(endTime)
        self.timeRangeLineEdit.setText(timeRangeString)

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
        #TODO: Sprawdzanie odpowiednie dane są dostępne na tym zakresie
        if not all(wave in self.compositeDataWrapper.data_waves for wave 
                   in self.procedure.required_waves):
            QW.QMessageBox.warning(self, "Błąd ogólny",
                                   "Nie ma wszystkich wymaganych przebiegów")
            return False
        if not all(points in self.compositeDataWrapper.data_points for points 
                   in self.procedure.required_points): 
            QW.QMessageBox.warning(self, "Błąd ogólny",
                                   "Nie ma wszystkich wymaganych punktów")
            return False
        arguments = self.procedureArgumentsWidget.getArguments()
        valid, message = self.procedure.validate_arguments(
            self.compositeDataWrapper, arguments)
        if not valid:
            QW.QMessageBox.warning(self, "Błąd argumentów",
                                   message)
            return False
        return True

    def addRequiredDataWidgets(self):
        requiredWavesText = "Wymagane przebiegi: "
        for requiredWave in self.procedure.required_waves:
            requiredWavesText+=requiredWave+" "
        requiredWavesLabel = QW.QLabel(requiredWavesText)
        self.vBoxLayout.addWidget(requiredWavesLabel)

        requiredPointsText = "Wymagane punkty: "
        for requiredPoints in self.procedure.required_points:
            requiredPointsText+=requiredPoints+" "
        requiredPointsLabel = QW.QLabel(requiredPointsText)
        self.vBoxLayout.addWidget(requiredPointsLabel)

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
        if self.dataActionStatus is DataActionStatus.Ok:
            selectedProcedureWidget = self.procedureWidgetDict[self.selectedProcedureName]
            beginTime, endTime = selectedProcedureWidget.getTimeRange()
            procedure = selectedProcedureWidget.procedure
            arguments = selectedProcedureWidget.getArguments()
            return beginTime, endTime, procedure, arguments
        else:
            return None, None, None, None

    @classmethod
    def getProcedure(cls, procedureType, compositeDataWrapper):
        procedureWidget = cls(procedureType, compositeDataWrapper)
        if not procedureWidget.exec_():
            procedureWidget.dataActionStatus = DataActionStatus.Cancel
        values = list(procedureWidget.getValues())
        values.append(procedureWidget.dataActionStatus)
        return tuple(values)
