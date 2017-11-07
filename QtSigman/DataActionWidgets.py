from enum import Enum, auto

from PyQt5 import QtWidgets as QW
from matplotlib import colors

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
    def __init__(self, title="", dictType="default", color="#1f77b4", forbiddenNames=[], 
                 parent=None, axis=Axis.Left, offset='0', askDelete=False):
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
            nazwa (type), kolor, oś"""
        dataSettingsWidget = cls(**kwargs)
        if not dataSettingsWidget.exec_():
            dataSettingsWidget.dataActionStatus = DataActionStatus.Cancel
        values = list(dataSettingsWidget.getValues())
        values.append(dataSettingsWidget.dataActionStatus)
        return tuple(values)

#TODO: Procedure list widget; Misc procedure window
