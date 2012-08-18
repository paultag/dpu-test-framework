# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests the workspace system
"""

from dpu.workspace import Workspace
from dpu.utils import abspath
import os

workspace = abspath("./tests/resources/workspace")


def test_test_finder():
    tests = os.listdir("%s/tests" % (workspace))
    ws = Workspace(workspace)
    for test in ws.tests():
        tests.remove(test.test_id)
    assert tests == []


def test_test_context():
    ws = Workspace(workspace)
    for test in ws.tests():
        assert test._context['foo'] != 'foo'
        assert test._context['bar'] == 'bar'
