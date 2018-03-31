#!/usr/bin/env python3
# This script tests if procedures in `procedures` directory work, at least
# insofar as they are valid and don't immediately crash upon import.

import sys
import os
_script_path = os.path.abspath(__file__)
_script_directory = os.path.dirname(_script_path)
_sigman_root_directory = os.path.dirname(_script_directory)
os.chdir(_script_directory)
sys.path.append(_sigman_root_directory)
import pytest

from sigman import analyzer

def test_procedure_list():
    list_ = analyzer.list_procedures()
    assert len(list_) > 0

@pytest.mark.parametrize("procedure_item", 
    analyzer.dictify_procedures().items())
def test_procedure_imports(procedure_item):
    module_name = procedure_item[0]
    module_path = procedure_item[1]
    proc_from_name = analyzer.import_procedure(module_name)
    proc_from_path = analyzer.import_procedure(module_path)
    assert proc_from_name.description == proc_from_path.description
