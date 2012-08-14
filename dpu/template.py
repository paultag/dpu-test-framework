# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import os
import subprocess
from dpu.util import dir_walk, rm
from jinja2 import Template


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
