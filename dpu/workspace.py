# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module manages the test workspace, and helps manage the tests.
"""
from dpu.templates import TemplateManager, JinjaTemplate
from dpu.utils import load_config, abspath
import os


class Test(object):
    """
    This is an object that is able to preform all the functions of building
    and running the test.
    """

    def __init__(self, path, test_id, workspace):
        """
        We require three arguments - a path to the test, a unique id, and the
        workspace object we fall back on.
        """
        self._test_path = path
        self._context = load_config("%s/test.json" % (path))
        self._workspace = workspace
        self._update_context()
        self.test_id = test_id

    def set_global_context(self, config):
        """
        Re-set the global context (or rather, set the context to this, updated
        with the current context).
        """
        cfg = config
        cfg.update(self._context)
        self._context = cfg
        self._update_context()

    def _update_context(self):
        """
        This is called after we update the context. This keeps the generated
        instance variables up to date.
        """
        self.name = self._context['testname']

    def get_source_and_version(self):
        """
        Get the test's source package name, and version.
        """
        return (self._context['source'],
                self._context['version'])

    def get_template_stack(self):
        """
        Get the template stack in the form of the TemplateManager.
        """
        ctx = self._context
        tm = TemplateManager()
        native = ctx['native']
        root_template = self._template_search(ctx['template'])
        debian = []
        upstream = ctx['upstream']

        pkgname, version = self.get_source_and_version()
        version = version['upstream']

        if native:
            tm.add_real_template(root_template)

        for template in upstream:
            tm.add_real_template(self.get_template(template))

        if not native:
            tm.add_template("UpstreamShim", pkgname, version)
            tm.add_template("DebianShim")
            tm.add_real_template(root_template)
            debian = ctx['debian']

        for template in debian:
            tm.add_real_template(self.get_template(template))

        return tm

    def get_template(self, name):
        """
        Get the template by the name of `name`, and return that, or None.
        """
        path = abspath("%s/%s" % (self._test_path, name))
        ctx = self._context
        if os.path.exists(path):
            return JinjaTemplate(path,
                                 context=ctx)
        return None

    def _template_search(self, name):
        """
        Internal search implementation. There be dragons here.
        """
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
        """
        Get a workspace global template by the name of `name`.
        """
        path = abspath("%s/templates/%s" % (self._workspace_path, name))
        if os.path.exists(path):
            return JinjaTemplate(path)
        return None

    def get_test(self, test):
        """
        Get a single test by the name of `test`.
        """
        fpath = os.path.join(self._test_dir, test)
        tobj = Test(fpath, test, self)
        tobj.set_global_context(self._context)
        return tobj

    def tests(self):
        """
        Get all the test to be handled
        """
        for test in os.listdir(self._test_dir):
            yield self.get_test(test)
