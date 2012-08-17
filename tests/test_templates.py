from dpu.templates import PlainTemplate, JinjaTemplate
from dpu.utils import tmpdir, cd
import os.path
import os


def assert_content(path, content):
    content_obj = open(path, 'r').read().strip()
    if content != content_obj:
        print "Path: %s" % (path)
        print "Expt: %s" % (content)
        print "Got:  %s" % (content_obj)

    assert content == content_obj


def test_plain_template_basic():
    with tmpdir() as tmp:
        pt1 = PlainTemplate("tests/resources/templates/plain1")
        pt1.render(tmp)
        with cd(tmp):
            for x in ['foo', 'bar', 'baz']:
                assert_content(x, x)


def test_plain_template_advanced():
    with tmpdir() as tmp:
        pt1 = PlainTemplate("tests/resources/templates/plain1")
        pt2 = PlainTemplate("tests/resources/templates/plain2")
        pt1.render(tmp)
        pt2.render(tmp)

        values = {
            "foo": "foo",
            "bar": "not bar",
            "baz": "baz",
            "kruft/flip": "flip"
        }

        with cd(tmp):
            for entry in values:
                content = values[entry]
                assert_content(entry, content)


def test_jinja_template_basic():
    with tmpdir() as tmp:
        jt1 = JinjaTemplate("tests/resources/templates/jinja1")

        context = {
            "foo": "foo1",
            "kruft": "kruft1",
            "plop": "plop1"
        }

        jt1.setContext(context)
        jt1.render(tmp)

        with cd(tmp):
            for x in context:
                if not os.path.exists(x):
                    assert os.path.exists(x)

            for entry in context:
                assert_content(entry, context[entry])


def test_jinja_template_advanced():
    with tmpdir() as tmp:
        jt1 = JinjaTemplate("tests/resources/templates/jinja1")
        jt2 = JinjaTemplate("tests/resources/templates/jinja2")

        context = {
            "foo": "foo1",
            "kruft": "kruft1",
            "plop": "plop1",
            "no": "no",
            "go": "go",
        }

        jt1.setContext(context)
        jt2.setContext(context)
        jt1.render(tmp)
        jt2.render(tmp)

        files = {
            "literal": "{{literal}}",
            "really/nested/directory/with/a/file/foo": context['foo'],
            "kruft": context['kruft'],
            "foo": context['foo'],
            "nogo": "%s %s" % (context['no'], context['go']),
            "plop": context['plop']
        }

        with cd(tmp):
            for f in files:
                assert_content(f, files[f])
