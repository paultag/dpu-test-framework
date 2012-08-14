# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

from dpu.util import cp, mkdir, disposabledir
from dpu.template import render_templates
import json
import os.path


def test_basics():
    templ_name = "templates-basic"
    staging = "tests/staging/%s" % (templ_name)
    with disposabledir("tests/staging/templates-basic"):
        cp("tests/resources/templates/%s" % (templ_name),
           staging)
        context = json.load(open("%s/%s/context.json" % (
            staging, templ_name
        ), 'r'))
        render_templates("%s/%s" % (staging, templ_name), context)

        assert open("%s/%s/%s" % (
            staging, templ_name, "test"
        ), 'r').read() == "baz"

        assert open("%s/%s/%s" % (
            staging, templ_name, "test2"
        ), 'r').read() == "bar"

        assert not os.path.exists("%s/%s/%s.tpl" % (
            staging, templ_name, "test"
        ))

        assert not os.path.exists("%s/%s/%s.tpl" % (
            staging, templ_name, "test2"
        ))
