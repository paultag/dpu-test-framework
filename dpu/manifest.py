# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

import os
from functools import partial
from collections import defaultdict


from dpu import (ENTRY_TYPE_DIR,
                 ENTRY_TYPE_FILE,
                 ENTRY_TYPE_SYMLINK)

from dpu.utils import unix_perm
from .exceptions import (InvalidManifestError,
                         SymlinkTargetAssertionError,
                         EntryPermissionAssertionError,
                         EntryPresentAssertionError,
                         EntryNotPresentAssertionError,
                         EntryWrongTypeAssertionError)


def _split_usergroup(value):
    user, group, re = value.split(":", 2)
    if re:
        raise InvalidManifestError('Too many colons in "user:group" argument')
    if not group:
        # allow "/" as separator (because tar uses it in tar -vt)
        user, group, re = value.split("/", 2)
        if re:
            raise InvalidManifestError(
                'user & group must be separated with ":" if they contain "/"')
    return (user, group)


def _is_present(entry, edata, data, present=True):
    if "present" in edata and edata["present"] != present:
        raise InvalidManifestError(
            "%s cannot be present and not-present at the same time" % (entry))
    edata["present"] = present
    if present:
        # if entry is present, then so is the dir containing it
        dirpart, _ = os.path.split(entry)
        if not dirpart:
            # its parent is the "root", stop here
            return
        dedata = data[dirpart]
        # This will "create" the parent dirs recursively
        _is_file_type(dirpart, dedata, ENTRY_TYPE_DIR, data)


def _is_file_type(entry, edata, etype, data):
    _is_present(entry, edata, data)
    if "entry-type" in edata:
        if edata["entry-type"] != etype:
            raise InvalidManifestError(
                "%s cannot be a %s and a %s at the same time" % (
                    entry, etype, edata["entry-type"]))
    else:
        edata["entry-type"] = etype

    if etype == ENTRY_TYPE_SYMLINK and "perm" in edata:
        raise InvalidManifestError(
            "%s is expected to be a symlink, but has perm information" % (
                entry
            ))


def _parse_link_target(data, cmd, last, arg):
    entry = last
    target = None
    if arg:
        args = arg.split(None, 3)
        if len(args) == 1 or len(args) == 2:
            target = args[0]
            if len(args) > 1:
                entry = args[1]
    if target is None:
        raise InvalidManifestError("%s takes either one or two arguments" % (
            cmd))

    edata = data[entry]
    _is_file_type(entry, edata, ENTRY_TYPE_SYMLINK, data)
    if "link-target" in edata and edata["link-target"] != target:
        raise InvalidManifestError(
            "%s cannot point to %s and %s at the same time" % (
                entry, target, edata["link-target"]))
    edata["link-target"] = target
    return entry


def _parse_not_present(data, cmd, last, arg):
    if not arg or len(arg.split(None, 1)) != 1:
        raise InvalidManifestError("%s takes exactly one argument" % cmd)
    entry = arg
    edata = data[entry]
    _is_present(entry, edata, data, present=False)
    return None


def _parse_contains_X(data, cmd, last, arg):
    etype = cmd.replace("contains-", "", 1)
    if not arg or len(arg.split(None, 1)) != 1:
        raise InvalidManifestError("%s takes exactly one argument" % cmd)
    entry = arg
    edata = data[entry]
    _is_file_type(entry, edata, etype, data)
    return entry


def _set_perm(entry, edata, mode, user, group):
    if "entry-type" in edata and edata["entry-type"] == ENTRY_TYPE_SYMLINK:
        raise InvalidManifestError("%s cannot be applied to symlink entry" % (
            entry))

    if "perm" in edata and edata["perm"] != mode:
        raise InvalidManifestError("Conflicting perm mode for %s" % entry)
    edata["perm"] = mode

    if user is not None:
        # TODO:
        # Problem here is that python-apt's "TarMember" does not expose
        # the user/group, only uid/gid
        raise NotImplementedError("user:group setting not implemented")


def _parse_contains_entry(data, cmd, last, arg):
    entry = None
    uperm = None
    user = None
    group = None
    if arg:
        args = arg.split(None, 3)
        if len(args) == 2 or len(args) == 3:
            uperm = args[0]
            entry = args[-1]
            if len(args) == 3:
                user, group = _split_usergroup(args[1])
    if entry is None:
        raise InvalidManifestError(
            "%s takes at least two and at most three arguments" % (cmd))
    edata = data[entry]
    ftype, mode = unix_perm(uperm)
    _is_file_type(entry, edata, ftype, data)
    _set_perm(entry, edata, mode, user, group)
    return entry


def _parse_perm(data, cmd, last, arg):
    entry = None
    mode = None
    user = None
    group = None
    if arg:
        args = arg.split(None, 4)
        if len(args) > 0 and len(args) < 4:
            mode = int(args[0], 8)
            entry = last
            if len(args) > 1:
                user, group = _split_usergroup(args[1])
            if len(args) == 3:
                entry = args[2]

    if entry is None:
        raise InvalidManifestError(
            "%s takes at least one and at most three arguments" % (cmd))

    edata = data[entry]
    _is_present(entry, edata, data)
    _set_perm(entry, edata, mode, user, group)

    return entry


def _not_implemented(data, cmd, last, arg):
    raise NotImplementedError("%s is not implemented" % cmd)

COMMANDS = {
    "contains-file": _parse_contains_X,
    "contains-dir": _parse_contains_X,
    "contains-symlink": _parse_contains_X,
    "not-present": _parse_not_present,
    "link-target": _parse_link_target,
    "perm": _parse_perm,
    "contains-entry": _parse_contains_entry,

    "same-content": _not_implemented,
    "hardlinks": _not_implemented,
}


def parse_manifest(fname):
    data = defaultdict(dict)
    with open(fname) as f:
        last = None
        for line in (l.strip() for l in f):
            if not line or line[0] == '#':
                continue
            spl = line.split(None, 1)
            if spl[0] not in COMMANDS:
                raise InvalidManifestError("Unknown command %s" % spl[0])
            if len(spl) == 1:
                spl.append(None)
            last = COMMANDS[spl[0]](data, spl[0], last, spl[1])
    return Manifest(data)


class Manifest(object):
    def __init__(self, data):
        self._data = data

    def check_tarball(self, tar):
        data = self._data
        missing = set(x for x in data if data[x]["present"])
        for tinfo in tar:
            normtname = self._normname(tinfo.name)
            if normtname is None or normtname not in data:
                continue
            self._check_tar_entry(data[normtname], normtname, tinfo)
            missing.discard(normtname)
        if missing:
            first = sorted(missing)[0]
            raise EntryPresentAssertionError(first)

    def check_apt_tarball(self, tar):
        data = self._data
        missing = set(x for x in data if data[x]["present"])
        tar.go(partial(self._apt_visit_tarball, missing))
        if missing:
            first = sorted(missing)[0]
            raise EntryPresentAssertionError(first)

    def _apt_visit_tarball(self, data, missing, tarmember, _):
        normtname = self._normname(tarmember.name)
        if normtname is None or normtname not in data:
            return
        self._check_tar_entry(data[normtname], normtname, tarmember)
        missing.discard(normtname)

    def _normname(self, normtname):
        if normtname == '.' or normtname == './':
            return None
        # If it has a leading /, keep it.  Regular tarballs usually don't, but
        # it possible to do.
        if normtname[0] != "/":
            # technically incorrect with ../ or ./../ stuff, but a real tarball
            # won't have that.
            normtname = normtname.lstrip("./")
        return normtname

    def _check_tar_entry(self, mentry, normtname, tarmember):
        assert mentry is not None
        assert "present" in mentry

        if not mentry["present"]:
            raise EntryNotPresentAssertionError(normtname)

        if "entry-type" in mentry:
            etype = mentry["entry-type"]
            ok = False
            if etype == ENTRY_TYPE_FILE:
                ok = tarmember.isfile() or tarmember.islnk()
            elif etype == ENTRY_TYPE_DIR:
                ok = tarmember.isdir()
            elif etype == ENTRY_TYPE_SYMLINK:
                ok = tarmember.issym()
            else:
                # XXX handle devices/sockets
                raise AssertionError(
                    "%s is present, but not a known type!? (expected: %s)" % (
                        normtname, etype))
            if not ok:
                raise EntryWrongTypeAssertionError(normtname, etype)

        if "link-target" in mentry:
            assert tarmember.issym()
            if mentry["link-target"] != tarmember.linkname:
                raise SymlinkTargetAssertionError(normtname,
                                                  mentry["link-target"],
                                                  tarmember.linkname)

        if "perm" in mentry:
            assert not tarmember.issym()
            if mentry["perm"] != tarmember.mode:
                raise EntryPermissionAssertionError(normtname,
                                                    mentry["perm"],
                                                    tarmember.mode)
