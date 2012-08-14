# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import tarfile
import subprocess
from contextlib import contextmanager


def make_orig_tarball(rundir, upname, upversion, compression="gzip"):
    """Create an orig tarball in the rundir

    This function will create a tarball suitable for being used as an
    "upstream" tarball for a non-native package.  The source of the
    tarball will be the directory called "%(upname)s-%(upversion)",
    which must exists in rundir.

    The tarball will be created in rundir and will be named according
    to dpkg-source's expectation.

    The optional "compression" parameter can be used to choose the
    compression of the tarball.  Supported values are "gzip", "bzip2",
    "xz" and "lzma".  NB: For non-native 1.0 source packages, only
    "gzip" should be used.

    Caveat: The function assumes anything in the "source" directory to
    be a part of the "upstream code".  Thus, if a debian/ dir is
    present it will be a part of the "upstream" tarball.
    """
    unpackdir = "%s-%s" % (upname, upversion)
    unpackpath = os.path.join(rundir, unpackdir)
    orig_tarball = "%s_%s.orig.tar" % (upname, upversion)
    with _open_tarfile(orig_tarball, compression) as tarobj:
        tarobj.add(unpackpath, arcname=unpackdir)


@contextmanager
def _open_tarfile(tarbase, compression):
    """Opens an open TarFile for the given compression

    This function opens a TarFile and possibly setups a compression
    pipeline.  It returns a tuple with two elements (tobj, closefn).
    tobj is the TarFile instance and closefn is a callable that will
    close the TarFile and (if needed) clean up the compression
    pipeline.
    """

    if compression == 'gzip' or compression == 'bzip2':
        ext = "gz"
        if compression == 'bzip2':
            ext = "bz2"
        m = "w:%s" % ext
        tarball = "%s.%s" % (tarbase, ext)
        tobj = tarfile.open(name=tarball, mode=m)
        yield tobj
        tobj.close()
        return

    if compression != "xz" and compression != "lzma":
        raise ValueError("Unknown compression %s" % compression)

    m = "w|"
    # assume compression == ext == command - holds for xz and lzma :>
    # also assume the compressor takes no arguments and writes to stdout
    tarball = "%s.%s" % (tarbase, compression)
    out = open(tarball, "w")
    compp = subprocess.Popen([compression], shell=False, stdin=subprocess.PIPE,
                             stdout=out, universal_newlines=False)
    tobj = tarfile.open(name=tarball, mode=m, fileobj=compp.stdin)
    yield tobj
    try:
        tobj.close()
        compp.stdin.close()
        compp.wait()
        if compp.returncode != 0:
            raise IOError("%s exited with %s" % (compression, compp.returncode))
    except:
        if compp.returncode is None:
            # something broke trouble and the process has not been reaped; kill
            # it (nicely at first)
            compp.terminate()
            compp.poll()
            if compp.returncode is None:
                compp.kill()
                compp.wait()
        # re-raise the exception
        raise
