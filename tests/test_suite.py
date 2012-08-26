# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests the workspace system
"""

from dpu.suite import TestSuite
from dpu.utils import abspath, tmpdir, mkdir
from dpu.exceptions import InvalidTemplate
import os

workspace = abspath("./tests/resources/workspace")


def test_test_finder():
    """
    Make sure we can resolve test folders correctly.
    """
    tests = os.listdir("%s/tests" % (workspace))
    ws = TestSuite(workspace)
    for test in ws.tests():
        tests.remove(test.test_id)
    assert tests == []


def test_crazy_things():
    """
    Make sure we can resolve test folders correctly.
    """
    ws = TestSuite(workspace)
    test = ws.get_test("cruft-empty-diff")
    assert test._template_search("hello") is not None
    assert test._template_search("generic") is not None
    try:
        test._template_search("hello-brainfuck")
        assert False is True
    except Exception:
        pass


def test_test_context():
    """
    Make sure the context overloader works correctly
    """
    ws = TestSuite(workspace)
    for test in ws.tests():
        assert test._context['foo'] != 'foo'
        assert test._context['bar'] == 'bar'


def test_run_all_the_things():
    """
    Test all the thingers.
    """
    ws = TestSuite(workspace)
    test = ws.get_test("cruft-empty-diff")
    source, version = test.get_source_and_version()
    version = version['upstream']

    tm = test.get_template_stack()
    with tmpdir() as tmp:
        path = "%s/%s-%s" % (tmp, source, version)
        mkdir(path)
        tm.render(path)


def test_upstream_shim():
    ws = TestSuite(workspace)
    test = ws.get_test("native-calls-upstream-shim")
    source, version = test.get_source_and_version()
    version = version['upstream']
    try:
        tm = test.get_template_stack()
    except InvalidTemplate:
        return
    assert True is False


def test_invalid_template():
    ws = TestSuite(workspace)
    test = ws.get_test("invalid-template-call")
    source, version = test.get_source_and_version()
    version = version['upstream']
    try:
        tm = test.get_template_stack()
    except InvalidTemplate:
        return
    assert True is False


def test_run_tests():
    """
    Test all the thingers.
    """
    ws = TestSuite(workspace)
    test = ws.get_test('cruft-empty-diff')
    test.run()


def test_templater():
    """
    Make sure we can render out templates correctly
    """
    ws = TestSuite(workspace)
    test = ws.get_test("cruft-empty-diff")
    source, version = test.get_source_and_version()
    version = version['upstream']

    tm = test.get_template_stack()
    with tmpdir() as tmp:
        path = "%s/%s-%s" % (tmp, source, version)
        mkdir(path)
        tm.render(path)
        # verify path...
