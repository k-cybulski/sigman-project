from os import getcwd

from PyQt5 import QtWidgets as QW
from sigman import file_manager as fm

from QtSigman import DataActionWidgets
from QtSigman.DataActionWidgets import DataActionStatus

def importLine(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        dataLine = fm.import_line(path[0])
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.data_lines.keys(),
            title = path[0])
        if status is DataActionStatus.Ok: 
            dataLine.offset = offset
            compositeDataWrapper.add_data_line(dataLine, dictType, 
                                               color, axis = axis)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def importPoints(compositeDataWrapper):
    fileFilter = "dat (*.dat)"
    fileDialog = QW.QFileDialog()
    fileDialog.setFileMode(QW.QFileDialog.ExistingFiles)
    try:
        path = fileDialog.getOpenFileName(filter = fileFilter)
        assert path[0] != ""
        dataPoints = fm.import_points(path[0])
        dictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
            forbiddenNames = compositeDataWrapper.data_points.keys(),
            title = path[0])
        if status is DataActionStatus.Ok:
            dataPoints.move_in_time(offset)
            compositeDataWrapper.add_data_points(dataPoints, dictType, color, axis = axis)
    # W wypadku, gdy plik nie zostanie wybrany, po prostu udajemy że nic się
    # nie stało i nic nie zmieniamy
    except AssertionError:
        pass

def editLineSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.data_lines.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.data_lines[dictType].axis,
        offset = str(compositeDataWrapper.data_lines[dictType].offset),
        askDelete = True,
        color = compositeDataWrapper.data_lines[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataLineSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_data_line(dictType)

def editPointSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.data_points.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.data_points[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.data_points[dictType].color)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataPointsSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_data_points(dictType)

def editParameterSettings(compositeDataWrapper, dictType):
    forbiddenNames = list(compositeDataWrapper.parameters.keys())
    forbiddenNames.remove(dictType)
    newDictType, color, axis, offset, status = DataActionWidgets.DataSettingsDialog.getDataSettings(
        forbiddenNames = forbiddenNames,
        dictType = dictType,
        title = dictType,
        axis = compositeDataWrapper.parameters[dictType].axis,
        askDelete = True,
        color = compositeDataWrapper.parameters[dictType].color,
        offset = None)
    if status is DataActionStatus.Ok:
        compositeDataWrapper.editDataPointsSettings(
            dictType, newDictType, color, axis, offset)
    if status is DataActionStatus.Delete:
        compositeDataWrapper.delete_parameter(dictType)
