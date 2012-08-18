# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module manages the test workspace, and helps manage the tests.
"""
from dpu.utils import load_config
import os


class Test(object):
    def __init__(self, path, test_id):
        self._test_path = path
        self._context = load_config("%s/test.json" % (path))
        self._update_context()
        self.test_id = test_id

    def set_global_context(self, config):
        cfg = config
        cfg.update(self._context)
        self._context = cfg
        self._update_context()

    def get_template_chain(self):
        pass

    def _update_context(self):
        self.name = self._context['testname']


class Workspace(object):
    def __init__(self, workspace):
        """
        The only argument `workspace' is given the root of the test directory.
        """
        self._workspace_path = workspace
        self._test_dir = "%s/tests" % (workspace)
        self._context = load_config("%s/context.json" % (workspace))

    def tests(self):
        for test in os.listdir(self._test_dir):
            fpath = os.path.join(self._test_dir, test)

            tobj = Test(fpath, test)
            tobj.set_global_context(self._context)

            yield tobj
