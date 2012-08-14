# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from functools import partial

from .tarball_helper import make_and_check_tarball

test_src = "test"
test_ver = "1.0"
rundir = "./tests/resources/"
expected = "%s-%s/foo" % (test_src, test_ver)

def visit_tarball(tar):
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

mctar=partial(make_and_check_tarball, "test_tarball", rundir, test_src, test_ver)

def test_gzip():
    mctar("gzip", visit_tarball)

def test_bzip2():
    mctar("bzip2", visit_tarball)

def test_xz():
    mctar("xz", visit_tarball)

def test_lzma():
    mctar("lzma", visit_tarball)

