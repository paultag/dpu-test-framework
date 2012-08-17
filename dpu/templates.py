from dpu.utils import rsync, tmpdir, dir_walk, rm, cd
from jinja2 import Template
import os


class PlainTemplate(object):
    def __init__(self, where):
        self._template_path = where

    def render(self, dest):
        rsync(self._template_path, dest)


class JinjaTemplate(PlainTemplate):
    def render(self, dest):
        with tmpdir() as tmp:
            PlainTemplate.render(self, tmp)
            with cd(tmp):
                for template in dir_walk(tmp, xtn=".tpl"):
                    with open(template, 'r') as fd:
                        tobj = Template(fd.read())
                        with open(template.rsplit(".", 1)[0], 'w') as obj:
                            obj.write(tobj.render(**self.context))
                    rm(template)
            rsync(tmp, dest)


    def setContext(self, context):
        self.context = context


class UpstreamShim(PlainTemplate):
    def render(self, dest):
        pass  # Tar up the dest to ../


class DebianShim(PlainTemplate):
    def render(self, dest):
        pass  # Remove any ./debian directory


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
