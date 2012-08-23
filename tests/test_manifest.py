# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

import os
import tarfile

from dpu.manifest import parse_manifest
from dpu.exceptions import *
from dpu.utils import tmpdir, rsync, mkdir, rm
from dpu.tarball import open_compressed_tarball


resources = "./tests/resources/"
rundir = "./tests/staging/"


def check_manifest(resdir, manifest):
    mfile = os.path.join(resources, resdir, manifest)
    return parse_manifest(mfile)


def check_tarball(resdir, tfilter=None, rootmod=None):
    test_res = os.path.join(resources, resdir)
    man = parse_manifest(os.path.join(test_res, "manifest"))
    tarroot = os.path.join(test_res, "root")
    if tfilter is None:
        tfilter = _tar_filter

    with tmpdir() as staging:
        if rootmod is not None:
            newroot = os.path.join(staging, "root")
            rsync(tarroot, newroot)
            tarroot = newroot
            rootmod(tarroot)
        tname = os.path.join(staging, "test.tar.gz")
        tf = tarfile.open(tname, mode="w:gz")
        tf.add(tarroot, arcname=".", filter=tfilter)

        tf.close()
        with open_compressed_tarball(tname) as tar:
            man.check_tarball(tar)


def _tar_filter(tarinfo):
    if len(tarinfo.name) > 1 and tarinfo.name.startswith("./"):
        # technically incorrect with ../ or ./../ stuff, but a real tarball
        # won't have that.
        tarinfo.name = tarinfo.name.lstrip("./")
    tarinfo.uname = "root"
    tarinfo.gname = "root"
    tarinfo.uid = 0
    tarinfo.gid = 0
    return tarinfo


def _break_symlink(tarinfo):
    t = _tar_filter(tarinfo)
    if t.issym() and t.name == "usr/share/doc/foo/symlink-source":
        t.linkname = "debian/rules"
    return t


def _break_mode(tarinfo):
    t = _tar_filter(tarinfo)
    if (t.isfile() or t.islnk()) and t.name == "usr/share/doc/foo/copyright":
        t.mode = 0777
    return t


def _break_present(tarinfo):
    t = _tar_filter(tarinfo)
    if t.name == "usr/share/doc/foo/copyright":
        return None
    return t


def _alter_root_break_type(rootdir):
    cpyf = os.path.join(rootdir, "usr/share/doc/foo/copyright")
    rm(cpyf)
    mkdir(cpyf)


def _alter_root_add_unexpected_file(rootdir):
    d = os.path.join(rootdir, "usr/random")
    mkdir(d)
    f = os.path.join(d, "place")
    with open(f, "w") as fd:
        fd.write("Not supposed to bere!")


def test_manifest():
    check_tarball("manifest-tarball")


def test_manifest_bad_symlink():
    try:
        check_tarball("manifest-tarball", tfilter=_break_symlink)
        raise AssertionError("Bad mojo! Method is not supposed to return normally")
    except SymlinkTargetAssertionError as e:
        assert e.entry == "usr/share/doc/foo/symlink-source"
        assert e.expected == "symlink-target"
        assert e.actual == "debian/rules" # yes, yes it does!
    except ManifestCheckError as e:
        raise AssertionError("Unexpected check failure %s" % str(e))


def test_manifest_bad_mode():
    try:
        check_tarball("manifest-tarball", tfilter=_break_mode)
        raise AssertionError("Bad mojo! Method is not supposed to return normally")
    except EntryPermissionAssertionError as e:
        assert e.entry == "usr/share/doc/foo/copyright"
        assert e.expected == 0644
        assert e.actual == 0777
    except ManifestCheckError as e:
        raise AssertionError("Unexpected check failure %s" % str(e))


def test_manifest_bad_type():
    try:
        check_tarball("manifest-tarball", rootmod=_alter_root_break_type)
        raise AssertionError("Bad mojo! Method is not supposed to return normally")
    except EntryWrongTypeAssertionError as e:
        assert e.entry == "usr/share/doc/foo/copyright"
        assert e.expected == "file"
        assert e.actual is None or e.actual == "dir"
    except ManifestCheckError as e:
        raise AssertionError("Unexpected check failure %s" % str(e))


def test_manifest_unexpected_file():
    try:
        check_tarball("manifest-tarball", rootmod=_alter_root_add_unexpected_file)
        raise AssertionError("Bad mojo! Method is not supposed to return normally")
    except EntryNotPresentAssertionError as e:
        assert e.entry == "usr/random/place"
    except ManifestCheckError as e:
        raise AssertionError("Unexpected check failure %s" % str(e))


def test_manifest_missing_file():
    try:
        check_tarball("manifest-tarball", tfilter=_break_present)
        raise AssertionError("Bad mojo! Method is not supposed to return normally")
    except EntryPresentAssertionError as e:
        assert e.entry == "usr/share/doc/foo/copyright"
    except ManifestCheckError as e:
        raise AssertionError("Unexpected check failure %s" % str(e))


def test_implicit_dir():
    try:
        check_manifest("manifests", "implicit-dirs")
    except IOError as e:
        assert str(e) == "usr cannot be a file and a dir at the same time"

