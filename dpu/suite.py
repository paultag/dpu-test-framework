# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module manages the test workspace, and helps manage the tests.
"""
from dpu.templates import TemplateManager, JinjaTemplate
from dpu.utils import (load_config, abspath, tmpdir,
                       mkdir)
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
        cfg = config.copy()
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
        pkgname, version = self.get_source_and_version()
        version = version['upstream']

        for template in ctx['templates']:
            if template == "shim:upstream":  # XXX: Better handling here.
                if native:
                    raise KeyError("Native thinger calling upstream")
                tm.add_template("UpstreamShim", pkgname, version)
                tm.add_template("DebianShim")
            else:
                tobj = self._template_search(template)
                if tobj is None:
                    raise KeyError("Can't find template %s" % (
                        template))  # XXX: Not such a stupid exception here.
                tm.add_real_template(tobj)
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
            if templ is not None:
                templ.set_context(self._context)
                return templ
        return local_search

    def run(self):
        if "todo" in self._context:
            return "todo"

        source, version = self.get_source_and_version()
        version = version['upstream']
        tm = self.get_template_stack()
        suite = self._workspace
        with tmpdir() as tmp:
            path = "%s/%s-%s" % (tmp, source, version)
            mkdir(path)
            tm.render(path)
            for (thing, runner) in [("builders", run_builder), ("checkers", run_checker)]:
                titer = ((x, suite._look_up(thing, x)) for x in self._context[thing])
                for (name, tpath) in titer:
                    if tpath is None:
                        raise Exception("No %s called %s available" % (thing, name))
                    runner([tpath, path])


class TestSuite(object):
    def __init__(self, workspace):
        """
        The only argument `workspace' is given the root of the test directory.
        """
        self._workspace_path = abspath(workspace)
        self._test_dir = "%s/tests" % (workspace)
        self._context = load_config("%s/context.json" % (workspace))

    def get_template(self, name):
        """
        Get a workspace global template by the name of `name`.
        """
        # XXX: throw together some logic here

        path = self._look_up("templates", name)
        if path is None:
            return None
        return JinjaTemplate(path)

    def _look_up(self, thing, name):
        """
        Returns the path to the "thing" called "name" in the workspace
        or in /usr/share/dpu.  Returns None if that thing does not
        exists.

        Thing is (usually) one of "templates", "builders" or
        "checkers".
        """
        for base in (self._workspace_path, "/usr/share/dpu"):
            path = os.path.join(base, thing, name)
            if os.path.exists(path):
                return path
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
