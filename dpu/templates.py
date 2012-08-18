# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.
"""
This module contains Template classes to aid with rendering out model files
into a test source directory.
"""

from dpu.utils import rsync, tmpdir, dir_walk, rm, abspath, rmdir
from dpu.tarball import make_orig_tarball
from jinja2 import Template
import os.path
import sys

_templates = sys.modules[__name__]


class PlainTemplate(object):
    """
    PlainTemplate classes manage the rendering of a model directory of all
    "real" files to a secondary directory. This is the most basic Template
    class there is.
    """

    def __init__(self, where):
        """
        `where' is a path (abs or rel) to the Template directory, to be
        rendered when one invokes `render()' on this class.
        """
        self._template_path = abspath(where)

    def render(self, dest):
        """
        `dest' is a path (abs or rel) to the output directory, or where to
        write the model files to.
        """
        dest = abspath(dest)
        rsync(self._template_path, dest)


class JinjaTemplate(PlainTemplate):
    """
    JinjaTemplate is a class to manage writing a model directory full of
    Jinja2 template files (marked with a .tpl extention) out to the output
    directory.
    """

    def render(self, dest):
        """
        `dest' is a path (abs or rel) to the output directory, or where to
        write the model files to. Be extra-sure to call setContext on this
        particular class, it's important to render out the Jinja context
        correctly.
        """
        dest = abspath(dest)

        with tmpdir() as tmp:
            PlainTemplate.render(self, tmp)
            for template in dir_walk(tmp, xtn=".tpl"):
                with open(template, 'r') as fd:
                    tobj = Template(fd.read())
                    with open(template.rsplit(".", 1)[0], 'w') as obj:
                        obj.write(tobj.render(**self.context))
                rm(template)
            rsync(tmp, dest)

    def setContext(self, context):
        """
        This sets the context (just treat it as a dict) to be used during the
        Jinja2 rendering process.
        """
        self.context = context


class UpstreamShim(PlainTemplate):
    """
    This "fake" Template is actually a hook into the Template rendering process
    to allow us to save the upstream tar.gz before we taint it with "Debian"
    stuff. This allows for non-native emulation.
    """

    def __init__(self, pkgname, version):
        """
        OK, we're overloading this because we don't need a model directory.
        """
        self.compression = "gzip"
        self.pkgname = pkgname
        self.version = version

    def setCompression(self, compression):
        self.compression = compression

    def render(self, dest):
        """
        We're actually rendering a tarball out, not files from a model
        directory. We also expect that `dest' is in pkgname-verson format,
        ready for taring up.
        """
        make_orig_tarball(dest, self.pkgname, self.version,
                          compression=self.compression,
                          outputdir=dest)


class DebianShim(PlainTemplate):
    """
    This "fake" Template is actually a hook to clean any upstream Debian
    directories out, before laying down some sanity.
    """

    def __init__(self):
        """
        OK, we're overloading this because we don't need a model directory.
        """
        pass  # Overload, we don't need an arg for a shim

    def render(self, dest):
        """
        We're actually just going to remove "%s/debian" % (dest), if it exists,
        to make sure we don't have upstream crap futzing with us.
        """
        debdir = "%s/debian" % (dest)
        if os.path.exists(debdir):
            rmdir(debdir)


class TemplateManager(object):
    def __init__(self):
        self._chain = []

    def _get_template(self, name):
        global _templates
        return getattr(_templates, name, None)

# Example:
#
# For non-native packages:
#
# PlainTemplate(upstream_global)
# PlainTemplate(test_upstream)
# UpstreamShim()
# DebianShim()
# JinjaTemplate(debian_global)
# JinjaTemplate(test_debian)
#
# For native packages:
#
# PlainTemplate(upstream_global)
# PlainTemplate(test_upstream)
# JinjaTemplate(debian_global)
# JinjaTemplate(test_debian)
