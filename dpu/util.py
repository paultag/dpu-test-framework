# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from contextlib import contextmanager
import subprocess
import os.path
import shutil
import os


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
def workin(path):
    with disposabledir(path):
        with cd(path):
            yield


def mkdir(folder, destroy_old=False):
    try:
        os.makedirs(folder)
    except OSError as e:
        if e.errno == 17:
            rmdir(folder)
            return mkdir(folder, destroy_old=False)


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
    return os.rename(source, dest)


def rmdir(path):
    return shutil.rmtree(path)


def abspath(folder):
    return os.path.abspath(folder)
