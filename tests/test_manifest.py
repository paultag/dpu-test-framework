# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

import os
import tarfile

from dpu.manifest import parse_manifest
from dpu.utils import tmpdir
from dpu.tarball import open_compressed_tarball


resources = "./tests/resources/"
rundir = "./tests/staging/"


def test_manifest():
    testname = "manifest-tarball"
    test_res = os.path.join(resources, testname)
    man = parse_manifest(os.path.join(test_res, "manifest"))
    with tmpdir() as staging:
        tname = os.path.join(staging, "test.tar.gz")
        tf = tarfile.open(tname, mode="w:gz")
        tf.add(os.path.join(test_res, "root"),
               arcname=".", filter=__tar_filter)  # XXX: Refactor (out?) filter
                                                  #  for python 2.6. - PRT
        tf.close()
        with open_compressed_tarball(tname) as tar:
            man.check_tarball(tar)


def __tar_filter(tarinfo):
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    tarinfo.uid = 0
    tarinfo.gid = 0
    return tarinfo
