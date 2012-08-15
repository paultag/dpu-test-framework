# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import subprocess
from jinja2 import Template
from email.Utils import formatdate

from dpu.util import dir_walk, rm, cd, load_conf, mkdir, rmdir


def copy_template_dir(skeldir, tsrcdir, targetdir, exclude_skel=None,
                      exclude_test_src=None):
    """
    Prototype helper to setup a basic test dir from a skeleton and a
    test source
    """
    def _run_rsync(source, target, excludes):
        cmd = ['rsync', '-rpc', source + "/", target + "/"]
        if excludes:
            cmd.extend("--exclude=%s" % x for x in excludes)
        subprocess.check_call(cmd, shell=False)

    _run_rsync(skeldir, targetdir, exclude_skel)
    if os.path.isdir(tsrcdir):
        _run_rsync(tsrcdir, targetdir, exclude_test_src)


def render_templates(rundir, context):
    for template in dir_walk(rundir, xtn=".tpl"):
        with open(template, 'r') as fd:
            tobj = Template(fd.read())
            with open(template.rsplit(".", 1)[0], 'w') as obj:
                obj.write(tobj.render(**context))
        rm(template)
        # print "I: Rendered: %s" % (template)


def prepare_test(root, test, test_path, path):
    obj = load_conf("%s/test.json" % (test_path))
    template = obj['template']
    template_dir = os.path.join(root, "templates", template)

    def _get_date():
        return formatdate()

    context = load_conf(os.path.join(template_dir, "context.json"))
    context.update(obj)
    context.update({
        "get_date": _get_date
    })

    if os.path.exists(path):
        rmdir(path)

    mkdir(path)
    copy_template_dir(template_dir,
                      test,
                      path)
    render_templates(path, context)


def run_test(root, name, path):
    prepare_test(root, name, path, "%s/%s/%s" % ("staging", path, name))


def run_tests(root):
    testdir = os.path.join(root, "tests")
    for test in os.listdir(testdir):
        test_path = "%s/%s" % (testdir, test)
        run_test(root, test, test_path)
