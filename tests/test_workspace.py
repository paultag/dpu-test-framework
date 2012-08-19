# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests the workspace system
"""

from dpu.workspace import Workspace
from dpu.utils import abspath, tmpdir, mkdir
import os

workspace = abspath("./tests/resources/workspace")


def test_test_finder():
    """
    Make sure we can resolve test folders correctly.
    """
    tests = os.listdir("%s/tests" % (workspace))
    ws = Workspace(workspace)
    for test in ws.tests():
        tests.remove(test.test_id)
    assert tests == []


def test_test_context():
    """
    Make sure the context overloader works correctly
    """
    ws = Workspace(workspace)
    for test in ws.tests():
        assert test._context['foo'] != 'foo'
        assert test._context['bar'] == 'bar'


def test_templater():
    """
    Make sure we can render out templates correctly
    """
    ws = Workspace(workspace)
    test = ws.get_test("test-one")
    source, version = test.get_source_and_version()
    version = version['upstream']

    tm = test.get_template_stack()
    with tmpdir() as tmp:
        path = "%s/%s-%s" % (tmp, source, version)
        mkdir(path)
        tm.render(path)
        # verify path...
