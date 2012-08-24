# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

import os
import json
import errno
import shutil
import os.path
import tempfile
import subprocess
from itertools import starmap, chain
from contextlib import contextmanager

flattern = chain.from_iterable


def load_config(fpath):
    return json.load(open(fpath, 'r'))


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


@contextmanager
def tmpdir():
    path = tempfile.mkdtemp()
    try:
        yield path
    finally:
        pass
    rmdir(path)


def mkdir(folder, destroy_old=False):
    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno == errno.EEXIST and destroy_old:
            rmdir(folder)
            return mkdir(folder, destroy_old=False)
        raise


def dir_walk(path, xtn=None):
    path_iter = lambda root, _, files: (os.path.join(root, f) for f in files)
    walkiter = flattern(starmap(path_iter, os.walk(path)))

    if xtn is not None:
        return (x for x in walkiter if x.endswith(xtn))
    return walkiter


def cp(source, dest):
    if os.path.isdir(source):
        new_name = os.path.basename(source)
        return shutil.copytree(source, "%s/%s" % (dest, new_name))
    else:
        return shutil.copy2(source, dest)


def link(source, dest):
    return os.symlink(source, dest)


def rm(file_name):
    return os.remove(file_name)


def mv(source, dest):
    if os.path.exists(dest) and os.path.isdir(dest):
        d = os.path.join(dest, os.path.basename(source))
        return os.rename(source, d)
    return os.rename(source, dest)


def rmdir(path):
    return shutil.rmtree(path)


def abspath(folder):
    return os.path.abspath(folder)


def rsync(source, target, excludes=None):
    cmd = ['rsync', '-arpc', source + "/", target + "/"]
    if excludes:
        cmd.extend("--exclude=%s" % x for x in excludes)
    subprocess.check_call(cmd, shell=False)


def run_command(cmd, output=False):

    out = open("/dev/null", "w")

    subprocess.check_call(cmd,
                          shell=False,
                          stderr=out,
                          stdout=out)


def run_builder(cmd):
    binary, path = cmd
    cmd = [binary, path]
    run_command(cmd)


def run_checker(cmd):
    binary, path = cmd
    cmd = [binary, path]
    run_command(cmd)


def is_identical_with_diff(from_file, to_file,
                           from_data=None, to_data=None, output_fd=None):
    """Make a unified diff between from_file and to_file

    If from_data is given, the contents of from_file is assumed to be
    from_data.

    If to_data is given, the contents of to_file is assumed to be
    to_data.

    At most one of from_data and to_data may be given.

    Returns True if the files are identical
    """

    # Implementation detail; we use diff -u rather than
    # difflib.unified_diff because the former knows better than to
    # vomit binary data to stdout and "I" am too lazy to re-implement
    # the "is-binary" check.

    from_label = from_file
    to_label = to_file
    data = None
    pstdin = None
    if from_data is not None and to_data is not None:
        raise ValueError("At least one of from_data and to_data must be None")
    if from_data is not None:
        data = from_data
        from_file = '-'
        pstdin = subprocess.PIPE
    elif to_data is not None:
        data = to_data
        to_file = '-'
        pstdin = subprocess.PIPE
    cmd = ['diff', '-u',
           '--label=%s' % from_label,
           from_file,
           '--label=%s' % to_label,
           to_file]

    proc = subprocess.Popen(cmd, stdin=pstdin, stdout=output_fd)
    if data is not None:
        proc.stdin.write(data)
        proc.stdin.close()
    ret = proc.wait()
    if ret and ret != 1:
        if ret > 0:
            errmsg = "%s died with %d" % (" ".join(cmd), ret)
        else:
            errmsg = "%s was killed by signal %d" % (" ".join(cmd), abs(ret))
        raise OSError(errmsg)

    return not ret
