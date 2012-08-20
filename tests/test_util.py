# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module tests some basics in the utils class.
"""

import os

from dpu.utils import (dir_walk, mkdir, tmpdir, cd,
                       is_identical_with_diff)

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


def test_is_identical_with_diff():
    """
    Ensure is_identical_with_diff works
    """
    diff_orig = os.path.join(resources, "util-diff", "orig")
    diff_newf = os.path.join(resources, "util-diff", "newf")
    with open(os.devnull, "w") as null_fd:
        # A file is identical with itself
        assert is_identical_with_diff(diff_orig, diff_orig, output_fd=null_fd)
        assert is_identical_with_diff(diff_newf, diff_newf, output_fd=null_fd)
        # The two files are different
        assert not is_identical_with_diff(diff_orig, diff_newf,
                                          output_fd=null_fd)

        assert not is_identical_with_diff(diff_newf, diff_orig,
                                          output_fd=null_fd)

        with open(diff_orig) as orig_fd:
            orig_data = orig_fd.read()
            # The files appear to be identical if we lie about diff_newf's
            # content
            assert is_identical_with_diff(diff_orig, diff_newf,
                                          to_data=orig_data, output_fd=null_fd)
            assert is_identical_with_diff(diff_newf, diff_orig,
                                          from_data=orig_data,
                                          output_fd=null_fd)

        with open(diff_newf) as newf_fd:
            newf_data = newf_fd.read()
            # The files appear to be identical if we lie about diff_orig's
            # content
            assert is_identical_with_diff(diff_orig, diff_newf,
                                          from_data=newf_data,
                                          output_fd=null_fd)

            assert is_identical_with_diff(diff_newf, diff_orig,
                                          to_data=newf_data,
                                          output_fd=null_fd)

        try:
            is_identical_with_diff(diff_orig, diff_newf, from_data='',
                                   to_data='', output_fd=null_fd)
            assert False
        except ValueError:
            pass
