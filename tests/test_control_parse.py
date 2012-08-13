from dpu.control import parse_control

def test_sanity():
    assert parse_control("tests/resources/sanity") == {"sane": "true"}

def test_sanity_caps():
    assert parse_control("tests/resources/sanity",
                         ignore_case=False) == {"Sane": "true"}

def test_sanity_nocaps():
    assert parse_control("tests/resources/sanity",
                         ignore_case=True) == {"sane": "true"}

def test_multiline():
    obj = parse_control("tests/resources/multiline")
    assert obj['test'] == "true"
    assert obj['description'] == """This is a super long line
with more then one block in

it."""
