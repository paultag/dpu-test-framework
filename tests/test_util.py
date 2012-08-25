# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests some basics in the utils class.
"""

import os

from dpu.utils import (dir_walk, mkdir, tmpdir, cd,
                       diff, diff_against_string,
                       parse_perm)

resources = "./tests/resources/"


def touch(fd):
    open(fd, 'a').close()


def test_basic_walk():
    """
    Test to make sure we can walk a directory.
    """
    with tmpdir() as t:
        with cd(t):
            mkdir("foo")
            mkdir("bar")
            mkdir("baz")

            targets = [
                "./foo/bar.target",
                "./foo/bar",
                "./bar/foo.target",
                "./baz/foo"
            ]

            for target in targets:
                touch(target)

            for entry in dir_walk("./"):
                assert entry in targets
                targets.remove(entry)

        assert targets == []


def test_more_walk():
    """
    Ensure s'more basics in walking a directory, with an extention
    filter.
    """
    with tmpdir() as t:
        with cd(t):
            mkdir("foo")
            mkdir("bar")
            mkdir("baz")

            valid_targets = [
                "./foo/bar.target",
                "./bar/foo.target",
                "./kruft.target"
            ]

            invalid_targets = [
                "./foo/bar",
                "./baz/foo",
                "./kruft"
            ]
            invalid_cmp = list(invalid_targets)

            for target in valid_targets + invalid_targets:
                touch(target)

            for entry in dir_walk("./", xtn='target'):
                if entry in valid_targets:
                    valid_targets.remove(entry)
                if entry in invalid_targets:
                    invalid_targets.remove(entry)

        assert valid_targets == []
        assert invalid_targets == invalid_cmp


def test_file_diff_ret():
    null = open("/dev/null", "w")
    assert not diff("tests/resources/util-diff/newf",
                    "tests/resources/util-diff/orig",
                    output_fd=null)


def test_file_diff_output():
    with tmpdir() as tmp:
        f = "%s/%s" % (tmp, "diff")
        fd = open(f, "w")
        assert not diff("tests/resources/util-diff/newf",
                        "tests/resources/util-diff/orig",
                        output_fd=fd)
        fd.close()

        cp1 = open(f, "r").read()
        cp2 = open("tests/resources/util-diff/diff", "r").read()
        assert cp1 == cp2


def test_string_diff_ret():
    null = open("/dev/null", "w")
    assert not diff_against_string("tests/resources/util-diff/newf",
                                   "tests/resources/util-diff/orig",
                                   output_fd=null)


def test_file_diff_output():
    cmp1 = """foo
bar
baz
"""
    with tmpdir() as tmp:
        f = "%s/%s" % (tmp, "diff.str")
        fd = open(f, "w")
        assert not diff_against_string("tests/resources/util-diff/newf",
                                       cmp1,
                                       output_fd=fd)
        fd.close()

        cp1 = open(f, "r").read()
        cp2 = open("tests/resources/util-diff/diff", "r").read()
        assert cp1 == cp2


def test_unix_perm():
    tests = {
        "-rw-r--r--": ("file", "0644")
    }
    for test in tests:
        typ1, mask1 = tests[test]
        typ2, mask2 = parse_perm(test)
        assert typ1 == typ2
        assert mask1 == mask2
