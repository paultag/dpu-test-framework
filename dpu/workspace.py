# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module manages the test workspace, and helps manage the tests.
"""
from dpu.utils import load_config
import os


class Test(object):
    def __init__(self, path, test_id, workspace):
        self._test_path = path
        self._context = load_config("%s/test.json" % (path))
        self._workspace = workspace
        self._update_context()
        self.test_id = test_id

    def set_global_context(self, config):
        cfg = config
        cfg.update(self._context)
        self._context = cfg
        self._update_context()

    def _update_context(self):
        self.name = self._context['testname']

    def get_template(self, name):
        path = abspath("%s/%s" % (self._test_path, name))
        if os.path.exists(path):
            return JinjaTemplate(path,
                                 context=self._context)
        return None

    def _template_search(self, name):
        local_search = self.get_template(name)
        if local_search is None:
            templ = self._workspace.get_template(name)
            templ.set_context(self._context)
            return templ
        return local_search


class Workspace(object):
    def __init__(self, workspace):
        """
        The only argument `workspace' is given the root of the test directory.
        """
        self._workspace_path = workspace
        self._test_dir = "%s/tests" % (workspace)
        self._context = load_config("%s/context.json" % (workspace))

    def get_template(self, name):
        path = abspath("%s/templates/%s" % (self._workspace_path, name))
        if os.path.exists(path):
            return JinjaTemplate(path)
        return None

    def get_test(self, test):
        fpath = os.path.join(self._test_dir, test)
        tobj = Test(fpath, test, self)
        tobj.set_global_context(self._context)
        return tobj

    def tests(self):
        for test in os.listdir(self._test_dir):
            yield self.get_test(test)
