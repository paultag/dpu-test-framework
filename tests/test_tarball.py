# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import tarfile
import subprocess
from contextlib import contextmanager

from dpu.tarball import make_orig_tarball
from dpu.util import workin


test_src = "test"
test_ver = "1.0"
the_path = "./tests/staging/"
rundir = "../../resources/"


def _compress(compression, xtn):
    with workin("%s/%s" % (the_path, compression)):
        make_orig_tarball(rundir, test_src, test_ver, compression=compression)
        path = "%s_%s.orig.tar.%s" % (test_src, test_ver, xtn)
        with _open_tarball(path, compression) as tar:
            expected = "%s-%s/foo" % (test_src, test_ver)
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



@contextmanager
def _open_tarball(tarball, compression):
    if compression == "gzip" or compression == "bzip2":
        tf = tarfile.open(tarball)
        yield tf
        tf.close()
    else:
        infd = open(tarball, "r")
        decomp = subprocess.Popen([compression, '-d'], shell=False, stdin=infd,
                                  stdout=subprocess.PIPE, universal_newlines=False)
        tobj = tarfile.open(name=tarball, mode="r|", fileobj=decomp.stdout)
        infd.close() # We don't need to keep this handle open
        yield tobj
        try:
            tobj.close()
            decomp.stdout.close()
            decomp.wait()
            if decomp.returncode != 0:
                raise IOError("%s exited with %s" % (compression, compp.returncode))
        except:
            if decomp.returncode is None:
                # something broke trouble and the process has not been reaped; kill
                # it (nicely at first)
                decomp.terminate()
                decomp.poll()
                if decomp.returncode is None:
                    decomp.kill()
                    decomp.wait()
            # re-raise the exception
            raise


def test_gzip():
    _compress("gzip", "gz")


def test_bzip2():
    _compress("bzip2", "bz2")

def test_xz():
    _compress("xz", "xz")

def test_lzma():
    _compress("lzma", "lzma")

