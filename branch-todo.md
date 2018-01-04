sigman/analyzer.py
    find_points and calculate_parameter should be more like modify_wave, i.e.
    they should take waves/points arguments
    These should be dicts that correspond to procedures' `required_waves` and
    `required_points`. Thankfully, we already have these lists.
    Validation would be similar to how it is already.
QtSigman/DataActionWidgets.py
    ProcedureDialog needs to accommodate wave/point choice like it does wave
    choice in `'modify'` case
QtSigman/DataActions.py
    findPoints needs to grab given waves and points in the `proc` variable
    it also needs to insert them into `analyzer.find_points`
