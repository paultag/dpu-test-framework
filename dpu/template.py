# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import sys
import subprocess
from jinja2 import Template
from email.Utils import formatdate

from dpu.util import dir_walk, rm, cd, load_conf, mkdir, rmdir, mv


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


def prepare_test(suite_dir, test, test_path, path):
    obj = load_conf("%s/test.json" % (test_path))
    template = obj['template']
    template_dir = os.path.join(suite_dir, "templates", template)

    def _get_date():
        return formatdate()

    context = load_conf(os.path.join(suite_dir, "context.json"))
    # OK, we've loaded the global context.
    context.update(load_conf(os.path.join(template_dir, "context.json")))
    context.update(obj)
    context.update({  # XXX: Break this out into some global dpu thing.
        "get_date": _get_date
    })

    if os.path.exists(path):
        rmdir(path)

    mkdir(path)
    copy_template_dir(template_dir,
                      test_path,
                      path)
    render_templates(path, context)
    return context


def run_class(suite_dir, workdir, context):

    exports = {
        "testname": "DPU_TEST_NAME",
        "src_pkg": "DPU_SRC_PACKAGE"
    }

    env = {}

    for export in exports:
        env[exports[export]] = context[export]

    full_version = context['version']['upstream']
    if "debian" in context['version']:
        full_version += "-%s" % (context['version']['debian'])
        env['DPU_DEBIAN_VERSION'] = context['version']['debian']

    env['DPU_SRC_VERSION'] = full_version
    env['DPU_UPSTREAM_VERSION'] = context['version']['upstream']

    binary = os.path.join(suite_dir, "classes", context['class'])

    subprocess.check_call([binary], env=env)


def run_test(suite_dir, name, path):
    print "I: Preparing %s" % (name)
    workdir = "%s/%s/%s" % ("staging", path, name)
    context = prepare_test(suite_dir, name, path, workdir)
    nwd = "%s-%s" % (workdir, context['version']['upstream'])

    if os.path.exists(nwd):
        rmdir(nwd)

    mv(workdir, nwd)
    workdir = nwd
    run_class(suite_dir, workdir, context)


def run_tests(suite_dir):
    testdir = os.path.join(suite_dir, "tests")
    for test in os.listdir(testdir):
        test_path = "%s/%s" % (testdir, test)
        run_test(suite_dir, test, test_path)
