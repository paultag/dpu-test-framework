# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from dpu.tarball import make_orig_tarball
from dpu.util import workin
import tarfile

test_src = "test"
test_ver = "1.0"
the_path = "./tests/staging/"
rundir = "../../resources/"


def _compress(compression, xtn):
    with workin("%s/%s" % (the_path, compression)):
        make_orig_tarball(rundir, test_src, test_ver, compression=compression)
        path = "%s_%s.orig.tar.%s" % (test_src, test_ver, xtn)
        with tarfile.open(path) as tar:
            member = tar.extractfile("%s-%s/foo" % (test_src, test_ver))
            assert member.read().strip() == "bar"


def test_gzip():
    _compress("gzip", "gz")


def test_bzip2():
    _compress("bzip2", "bz2")


# XXX: Implment LZMA / XZ
#      - PRT
