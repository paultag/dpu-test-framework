# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module manages the test workspace, and helps manage the tests.
"""
from dpu.templates import TemplateManager, JinjaTemplate
from dpu.exceptions import (InvalidTemplate, NoSuchCallableError,
                            InvalidContextFile)
from dpu.utils import (load_config, abspath, tmpdir,
                       mkdir, run_builder, run_checker,
                       diff, run_command)
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
            if template == "shim:upstream":
                if native:
                    raise InvalidTemplate("shim:upstream")
                tm.add_template("UpstreamShim", pkgname, version)
                tm.add_template("DebianShim")
            else:
                tobj = self._template_search(template)
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

    def _run_hook(self, stage, path="."):
        bin_path = "%s/%s" % (self._test_path, stage)
        if os.path.exists(bin_path):
            run_command([bin_path, path],
                        output=True)

    def _run_checks(self):
        # XXX: TODO: If check is a list, put together a pipeline.
        checks = self._context['checkers']
        for check in checks:
            path = self._workspace._look_up('checkers', check)
            run_checker(path, self.path)

    def _run_builds(self):
        builds = self._context['builders']
        for build in builds:
            path = self._workspace._look_up('builders', build)
            run_builder(path, self.path)

    def run(self, verbose=False):
        templates = self._context['templates'][:]
        templates.reverse()

        for template in templates:
            template = "%s.json" % (template)

            try:
                context = self._workspace._look_up('contexts', template)
                context = load_config(context)
                self.set_global_context(context)
            except NoSuchCallableError as e:
                pass

        self._run_hook("init")

        if "todo" in self._context:
            return {}

        source, version = self.get_source_and_version()
        version = version['upstream']
        tm = self.get_template_stack()
        with tmpdir() as tmp:
            self.path = "%s/%s-%s" % (tmp, source, version)
            path = self.path
            mkdir(path)
            self._run_hook("tmpdir", path=tmp)
            tm.render(path)

            self._run_hook("pre-build", path=path)
            self._run_builds()
            self._run_hook("post-build", path=path)

            self._run_hook("pre-check", path=path)
            self._run_checks()
            self._run_hook("post-check", path=path)

            results = {}
            for checker in self._context['checkers']:
                pristine = "%s/%s" % (self._test_path, checker)
                output = "%s/%s" % (tmp, checker)
                if os.path.exists(pristine):
                    # OK, let's verify
                    if os.path.exists(output):
                        with open("/dev/null", "w") as null:
                            if diff(pristine, output,
                                    output_fd=null):
                                results[checker] = "passed"
                            else:
                                results[checker] = "failed"
                                if verbose:
                                    print "================================"
                                    print "Checker match failure:"
                                    print "  -> %s" % (self.name)
                                    print "  -> %s" % (checker)
                                    print "--------------------------------"
                                    diff(pristine, output)
                                    print "================================"
                    else:
                        results[checker] = "no-output"
                else:
                    results[checker] = "no-pristine"
            self._run_hook("finally", path=path)
        return results


class TestSuite(object):
    def __init__(self, workspace):
        """
        The only argument `workspace' is given the root of the test directory.
        """
        self._workspace_path = abspath(workspace)
        self._test_dir = "%s/tests" % (workspace)
        context_file = os.path.join(workspace, "context.json")
        self._context = load_config(context_file)
        self._workspace = workspace
        try:
            self.name = self._context['suite-name']
        except KeyError:
            raise InvalidContextFile(context_file, "Missing suite-name")


    def get_template(self, name):
        """
        Get a workspace global template by the name of `name`.
        """
        try:
            path = self._look_up("templates", name)
        except NoSuchCallableError:
            raise InvalidTemplate("No such template: %s" % (name))

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
        raise NoSuchCallableError("No %s called %s available"
                                  % (thing, name))

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
        return (self.get_test(t) for t in os.listdir(self._test_dir))
