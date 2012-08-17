# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

import os
import tarfile
import subprocess
from contextlib import contextmanager


def make_orig_tarball(rundir, upname, upversion, compression="gzip",
                      outputdir=None):
    """Create an orig tarball in the rundir

    This function will create a tarball suitable for being used as an
    "upstream" tarball for a non-native package.  The source of the
    tarball will be the directory called "%(upname)s-%(upversion)",
    which must exists in rundir.

    The tarball will be created in outputdir and will be named
    according to dpkg-source's expectation.  If outputdir is not
    specified, it defaults to rundir.

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
    if outputdir is None:
        outputdir = rundir
    orig_tarball = os.path.join(outputdir, "%s_%s.orig.tar" % (
        upname,
        upversion
    ))
    with _open_writeable_tarfile(orig_tarball, compression) as tarobj:
        tarobj.add(unpackpath, arcname=unpackdir)


@contextmanager
def open_compressed_tarball(tarname, compression=None, fd=None):
    """Opens a compressed tarball in read-only mode as a TarFile

    This context manager transparently handles compressions unsupported
    by TarFile by using external processes.  The following compressions
    are supported "gzip", "bzip2", "xz" and "lzma".

    As the decompression may be done by an external process, seeking is
    generally not supported.

    tarname is the name of the tarfile.  If fd is None, this is the
    path to the tarball.  It is also passed to tarfile.open as the
    name parameter.

    compression is the compression type (see above for valid values).
    This can be omitted when the filename extension matches one of
    the supported compression methods.

    The optional parameter fd must be a file-like object opened for
    reading.  When given, the "content" of the tarball is read from fd
    rather than the file denoted by tarname.  This is useful for cases
    where the tarball is embedded inside another file (e.g. like the
    control.tar.gz in a .deb file).
    """

    if compression is None:
        compression = _determine_compression(tarname)
    if compression == "gzip" or compression == "bzip2":
        if fd is None:
            tf = tarfile.open(tarname)
        else:
            m = "r|gz"
            if compression == "bzip2":
                m = "r|bz2"
            tf = tarfile.open(name=tarname, mode=m, fileobj=fd)
        yield tf
        tf.close()
    else:
        infd = fd
        if infd is None:
            infd = open(tarname, "r")
        decomp = subprocess.Popen([compression, '-d'], shell=False, stdin=infd,
                                  stdout=subprocess.PIPE,
                                  universal_newlines=False)
        tobj = tarfile.open(name=tarname, mode="r|", fileobj=decomp.stdout)
        if fd is None:
            infd.close()  # We don't need to keep this handle open
        yield tobj
        _close_pipeline(tobj, decomp.stdout, decomp, compression)


@contextmanager
def _open_writeable_tarfile(tarbase, compression):
    """Opens an open TarFile for the given compression

    This opens a writable TarFile and compresses it with the specified
    compression.  The compression may be done by a pipeline and thus
    the TarFile may not be seekable.

    Supported compressions are "gzip", "bzip2", "xz" and "lzma".
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
    out.close()  # We don't need to keep this handle open
    tobj = tarfile.open(name=tarball, mode=m, fileobj=compp.stdin)
    yield tobj
    _close_pipeline(tobj, compp.stdin, compp, compression)


def _close_pipeline(tobj, procfd, proc, compression):
    try:
        tobj.close()
        procfd.close()
        proc.wait()
        if proc.returncode != 0:
            raise IOError("%s exited with %s" % (compression, proc.returncode))
    except:
        if proc.returncode is None:
            # something broke trouble and the process has not been reaped; kill
            # it (nicely at first)
            proc.terminate()
            proc.poll()
            if proc.returncode is None:
                proc.kill()
                proc.wait()
        # re-raise the exception
        raise

def _determine_compression(filename):
    ext = os.path.splitext(filename)[1]
    if not ext:
        raise ValueError("Cannot guess compression for %s" % filename)
    ext = ext[1:]
    if ext == "gz":
        return "gzip"
    if ext == "bz2":
        return "bzip2"
    if ext == "xz" or ext == "lzma":
        return ext
    raise ValueError("Cannot guess compression for %s" % filename)
