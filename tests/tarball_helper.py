# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from contextlib import contextmanager
import tarfile
import subprocess

from dpu.tarball import make_orig_tarball
from dpu.util import workin

the_path = "./tests/staging/"

@contextmanager
def open_compressed_tarball(tarball, compression):
    """Opens a compressed tarball in read-only mode

    This context manager transparently handles compressions unsupported
    by TarFile by using external processes.  The following compressions
    are supported "gzip", "bzip2", "xz" and "lzma".
    """
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
