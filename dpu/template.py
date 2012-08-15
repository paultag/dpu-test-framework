# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import subprocess
from jinja2 import Template

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


def prepare_test(test, test_path, path):
    obj = load_conf("%s/test.json" % (test_path))
    template = obj['template']

    context = load_conf("%s/%s/context.json" % ("templates", template))
    context.update(obj)

    if os.path.exists(path):
        rmdir(path)

    mkdir(path)
    copy_template_dir("%s/%s/template" % ("templates", template),
                      test,
                      path)
    render_templates(path, context)


def run_test(name, path):
    prepare_test(name, path, "%s/%s" % ("staging", path))


def run_tests(root):
    with cd(root):
        tests = os.listdir("tests")
        for test in tests:
            test_path = "%s/%s" % ("tests", test)
            run_test(test, test_path)
