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
    out = None
    if not output:
        out = open("/dev/null", "w")
    try:
        subprocess.check_call(cmd,
                              shell=False,
                              stderr=out,
                              stdout=out)
    finally:
        if out is not None:
            out.close()

def run_builder(cmd):
    run_command(list(cmd))


def run_checker(cmd):
    run_command(list(cmd))


def diff(from_file, to_file, output_fd=None):
    cmd = ['diff', '-u',
           '--label=%s' % from_file,
           from_file,
           '--label=%s' % to_file,
           to_file]
    proc = subprocess.Popen(cmd, stdout=output_fd)
    ret = proc.wait()
    return ret == 0


def diff_against_string(from_file, to_string, output_fd=None):
    cmd = ['diff', '-u',
           '--label=%s' % from_file,
           from_file,
           '--label=%s' % "-",
           "-"]
    proc = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=output_fd)
    if to_string is not None:
        proc.stdin.write(to_string)
        proc.stdin.close()
    ret = proc.wait()
    return ret == 0
