# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests some basics in the utils class.
"""

import os
from dpu.utils import dir_walk, mkdir, tmpdir, cd

def touch(fd):
    open(fd, 'a').close()

def test_basic_walk():
    """
    Test to make sure we can walk a directory.
    """
    with tmpdir("./tests/staging/test-basic-walk"):
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
