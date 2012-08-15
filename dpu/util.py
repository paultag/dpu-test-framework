# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import json
import errno
import shutil
import os.path
from itertools import starmap, chain
from contextlib import contextmanager

flattern = chain.from_iterable


def load_conf(path):
    return json.load(open(path, 'r'))


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


@contextmanager
def disposabledir(path):
    mkdir(path)
    try:
        yield
    finally:
        rmdir(path)


@contextmanager
def tmpdir(path):
    with disposabledir(path):
        with cd(path):
            yield

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
    if os.path.isdir(source):
        cp(source, dest)
        rmdir(source)
    else:
        return os.rename(source, dest)


def rmdir(path):
    return shutil.rmtree(path)


def abspath(folder):
    return os.path.abspath(folder)


def touch(fpath):
    open(fpath, 'a').close()
