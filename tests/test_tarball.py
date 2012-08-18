# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

from dpu.tarball import (open_compressed_tarball, make_orig_tarball,
                         _determine_compression)

from .tarball_helper import make_and_check_tarball
from dpu.utils import tmpdir, cd, mkdir
from functools import partial
import os.path
import os

test_src = "test"
test_ver = "1.0"
rundir = "./tests/resources/"
expected = "%s-%s/foo" % (test_src, test_ver)


def visit_open_tarball(tar):
    # We have to iterate through the tarball to ensure no seeking is done
    # (not possible when we decompress with a pipeline)
    for tinfo in tar:
        name = tinfo.name
        if name == "." or name.startswith("./"):
            # Currently tarballs members are not created with
            # "./", but it is not an error if they were.
            if name == "." or name == "./":
                # "root" dir, skip that entirely
                continue
            name = name[2:]

        if tinfo.isdir:
            # We expect this to be the directory "foo" is in
            assert expected.startswith(tinfo.name)
            continue

        if tinfo.isfile:
            assert tinfo.name == expected
            member = tar.extractfile(tinfo)
            assert member.read().strip() == "bar"
        else:
            # We should not get here
            print "Unexpected tarball member: %s" % tinfo.name
            assert False


def visit_tarball_path(tarpath, compression=None):
    with open(tarpath, "rb") as f:
        with open_compressed_tarball(tarpath, compression, fd=f) as tar:
            visit_open_tarball(tar)


make_visitor = lambda comp: partial(visit_tarball_path, compression=comp)


mctar = partial(make_and_check_tarball, "test_tarball",
                rundir, test_src, test_ver)


def test_localdir_generation():
    pkgname = "pkgfoo"
    version = "2.0"
    debdir = "%s-%s" % (pkgname, version)
    compression = "bzip2"
    tarball = "%s_%s.orig.tar.bz2" % (pkgname, version)

    with tmpdir() as tmp:
        with cd(tmp):
            mkdir(debdir)
            assert not os.path.exists(tarball)
            make_orig_tarball(".", pkgname, version,
                              compression=compression)
            assert os.path.exists(tarball)


def test_insane_compression_fails():
    pkgname = "pkgfoo"
    version = "2.0"
    debdir = "%s-%s" % (pkgname, version)

    with tmpdir() as tmp:
        with cd(tmp):
            mkdir(debdir)
            try:
                make_orig_tarball(".", pkgname, version,
                                  compression="asfasf")
                assert True is False
            except ValueError:
                assert True is True


def test_compression_guesser():
    things = {
        "foo.tar.gz": "gzip",
        "foo.tar.bz2": "bzip2",
        "foo.tar.xz": "xz",
        "foo.tar.lzma": "lzma"
    }
    for thing in things:
        assert things[thing] == _determine_compression(thing)

    insane = ['foo', 'bar.baz']
    for thing in insane:
        try:
            _determine_compression(thing)
            assert True is False
        except ValueError:
            assert True is True


def test_gzip():
    mctar("gzip", visit_open_tarball)


def test_bzip2():
    mctar("bzip2", visit_open_tarball)


def test_xz():
    mctar("xz", visit_open_tarball)


def test_lzma():
    mctar("lzma", visit_open_tarball)


def test_gzip_pipe():
    mctar("gzip", make_visitor("gzip"), visit_open=False)


def test_bzip2_pipe():
    mctar("bzip2", make_visitor("bzip2"), visit_open=False)


def test_xz_pipe():
    mctar("xz", make_visitor("xz"), visit_open=False)


def test_lzma_pipe():
    mctar("lzma", make_visitor("lzma"), visit_open=False)


def test_gzip_pipe_guess():
    mctar("gzip", visit_tarball_path, visit_open=False)


def test_bzip2_pipe_guess():
    mctar("bzip2", visit_tarball_path, visit_open=False)


def test_xz_pipe_guess():
    mctar("xz", visit_tarball_path, visit_open=False)


def test_lzma_pipe_guess():
    mctar("lzma", visit_tarball_path, visit_open=False)
