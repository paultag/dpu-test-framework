# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

import subprocess


def copy_template_dir(skeldir, tsrcdir, targetdir, exclude_skel=None,
                      exclude_test_src=None):
    """
    Prototype helper to setup a basic test dir from a skeleton and a
    test source
    """
    def _run_rsync(source, target, excludes):
        cmd = ['rsync', '-rpc', source + "/", target + "/"]
        if excludes:
            cmd.extend(exclude_skel)
        subprocess.check_call(cmd, shell=False)

    _run_rsync(skeldir, targetdir, exclude_skel)
    if os.path.isdir(tsrcdir):
        _run_rsync(tsrcdir, targetdir, exclude_test_src)
