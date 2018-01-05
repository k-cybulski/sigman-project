sigman/analyzer.py - done, not tested
    find_points and calculate_parameter should be more like modify_wave, i.e.
    they should take waves/points arguments
    These should be dicts that correspond to procedures' `required_waves` and
    `required_points`. Thankfully, we already have these lists.
    Validation would be similar to how it is already.
QtSigman/DataActionWidgets.py
    ProcedureDialog needs to accommodate wave/point choice like it does wave
    choice in `'modify'` case
    hence `ProcedureWidget.addRequiredDataWidgets` needs to be investigated
    `getSelectedWaveType` -> `getSelectedWaveDicts` and `getSelectedPointDicts`
    if `'modify'`, required_waves := "Wybrany przebieg"
    There should be widget containing a few DataArgumentWidgets
    it should have a "getSelection" that returns a dict of answers
    that would be reasonable
QtSigman/DataActions.py
    findPoints needs to grab given waves and points in the `proc` variable
    it also needs to insert them into `analyzer.find_points`

and finally, sigman/analyzer.py documentation needs to be done
