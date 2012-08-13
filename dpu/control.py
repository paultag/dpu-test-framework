# Copyright (c) GNU GPL-2+, dpu-test-framework authors.

def parse_control(file_name, ignore_case=True):
    """
    parse_control accepts a file name (abs or rel) to a dpu "control" file. dpu
    control files are really similar to Debian control files, and follow the
    same basic structure.

    The param "ignore_case" lets us know if we should ignore the casing of
    the keys in the control file.

    We return a dict
    """
    lines = open(file_name, 'r').readlines()
    key = None
    ret = {}

    for line in lines:
        if line[0] == ' ':
            if line == " .\n":
                line = ""  # We insert the newline below
            ret[key] += "\n%s" % (line.strip())
        else:
            key, val = line.split(":", 1)
            if ignore_case:
                key = key.lower()
            ret[key] = val.strip()

    if None in ret:
        del(ret[None])
    return ret
