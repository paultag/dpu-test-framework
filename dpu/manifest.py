def __get_edata(entry, data):
    if entry not in data:
        data[entry] = {}
    return data[entry]

def __is_present(entry, edata, present=True):
    if "present" in edata and edata["present"] != present:
        raise IOError("%s cannot be present and not-present at the same time" %
                      (entry))
    edata["present"] = present

def __is_file_type(entry, edata, etype):
    __is_present(entry, edata)
    if "entry-type" in edata:
        if edata["entry-type"] != etype:
            raise IOError("%s cannot be a %s and %s at the same time" %
                          (entry, etype, edata["entry-type"]))
    else:
        edata["entry-type"] = etype

def __parse_link_target(data, cmd, last, arg):
    entry = last
    target = None
    if arg:
        args = arg.split(None, 3)
        if len(args) == 1 or len(args) == 2:
            target = args[0]
            if len(args) > 1:
                entry = args[1]
    if target is None:
        raise IOError("%s takes either one or two arguments" % (cmd))

    edata = __get_edata(entry, data)
    __is_file_type(entry, edata, ENTRY_TYPE_SYMLINK)
    if "link-target" in edata and edata["link-target"] != target:
        raise IOError("%s cannot point to %s and %s at the same time" %
                      (entry, target, edata["link-target"]))
    edata["link-target"] = target
    return entry

def __parse_not_present(data, cmd, last, arg):
    if not arg or len(arg.split(None, 1)) != 1:
        raise IOError("%s takes exactly one argument" % cmd)
    entry = arg
    edata = __get_edata(entry, data)
    __is_present(entry, edata, False)
    return None

def __parse_contains_X(data, cmd, last, arg):
    etype = cmd.replace("contains-", "", 1)
    if not arg or len(arg.split(None, 1)) != 1:
        raise IOError("%s takes exactly one argument" % cmd)
    entry = arg
    edata = __get_edata(entry, data)
    __is_file_type(entry, edata, etype)
    return entry

def __not_implemented(data, cmd, last, arg):
    raise NotImplementedError("%s is not implemented" % cmd)

COMMANDS={
    "contains-file": __parse_contains_X,
    "contains-dir": __parse_contains_X,
    "contains-symlink": __parse_contains_X,
    "not-present":__parse_not_present,
    "link-target":__parse_link_target,

    "contains-entry":__not_implemented,
    "same-content":__not_implemented,
    "perm":__not_implemented,
    "hardlinks":__not_implemented,
}

ENTRY_TYPE_FILE="file"
ENTRY_TYPE_DIR="dir"
ENTRY_TYPE_SYMLINK="symlink"

def parse_manifest(fname):
    data = {}
    with open(fname) as f:
        last = None
        for line in (l.lstrip() for l in f):
            if not line or line[0] == '#':
                continue
            spl = line.split(None, 2)
            if spl[0] not in COMMANDS:
                raise IOError("Unknown command %s" % spl[0])
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
            normtname = self.__normname(tinfo.name)
            if normtname is None or normtname not in data:
                continue
            self.__check_tar_entry(data[normtname], normtname, tinfo)
            missing.discard(normtname)
        if missing:
            first = sorted(missing)[0]
            raise AssertionError("Missing %s" % first)

    def check_apt_tarball(self, tar):
        data = self._data
        missing = set(x for x in data if data[x]["present"])
        tar.go(parial(self.__apt_visit_tarball, missing))
        if missing:
            first = sorted(missing)[0]
            raise AssertionError("Missing %s" % first)

    def __apt_visit_tarball(self, data, missing, tarmember, _):
        normtname = self.__normname(tarmember.name)
        if normtname is None or normtname not in data:
            return
        self.__check_tar_entry(data[normtname], normtname, tarmember)
        missing.discard(normtname)

    def __normname(self, normtname):
        if normtname == '.' or normtname == './':
            return None
        # If it has a leading /, keep it.  Regular tarballs usually don't, but
        # it possible to do.
        if normtname[0] != "/":
            # technically incorrect with ../ or ./../ stuff, but a real tarball
            # won't have that.
            normtname = normtname.lstrip("./")        
        return normtname

    def __check_tar_entry(self, mentry, normtname, tarmember):
        # XXX: Maybe AssertionError is a bad choice
        if not mentry or "present" not in mentry:
            # We have no information on it
            return
        if not mentry["present"]:
            raise AssertionError("%s is not supposed to be present" % normtname)

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
                raise AssertionError("%s is present, but not a known type!? (expected: %s)"
                                     % (normtname, etype))
            if not ok:                    
                raise AssertionError("%s is present but not a %s" % (normtname, etype))

        if "link-target" in mentry:
            assert tarmember.issym()
            if mentry["link-target"] != tarmember.linkname:
                raise AssertionError("%s is a symlink, but points to %s intead of %s" % \
                                         (normtname, tarmember.linkname, mentry["link-target"]))
        if "perm" in mentry:
            assert not tarmember.issym()
            if mentry["perm"] != tarmember.mode:
                raise AssertionError("%s is mode 0%o instead of 0%o" %
                                     (normtname, mentry["perm"], tarmember.mode))
