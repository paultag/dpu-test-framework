# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from contextlib import contextmanager
import tarfile
import subprocess

from dpu.tarball import make_orig_tarball, open_compressed_tarball
from dpu.util import workin

the_path = "./tests/staging/"


def make_and_check_tarball(testname, rundir, upname, upversion, compression, visitor):
    """Create, check and clean up a tarball (test utility)

    Utility for setting up a dir, compile a tarball from a resource path, opening
    the tarball and passing it to vistor.

    testname is used to create a unique name for the test.  The
    compression is also used for this purpose, so multiple tests can
    share the same "testname" as long as the compression differs.

    rundir, upname, upversion and compression are passed (as is) to
    make_orig_tarball.

    The tarball passed to visitor may not be seekable and should be
    checked inorder.
    """

    xtn = compression
    if xtn == "gzip":
        xtn = "gz"
    elif xtn == "bzip2":
        xtn = "bz2"
    with workin("%s/%s-%s" % (the_path, testname, compression)):
        make_orig_tarball(rundir, upname, upversion, compression=compression)
        path = "%s_%s.orig.tar.%s" % (upname, upversion, xtn)
        with open_compressed_tarball(path, compression) as tar:
            visitor(tar)
