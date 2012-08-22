# Copyright (c) DPU AUTHORS, under the terms and conditions of the GPL-2+
# license.

class ManifestCheckError(Exception):
    def __init__(self, entry, expected=None, actual=None):
        self.entry = entry
        self.expected = expected
        self.actual = actual

    def __str__(self):
        raise NotImplementedError("Should have been overriden")


class EntryPresentAssertionError(ManifestCheckError):
    def __str__(self):
        return "Expected entry %s is missing" % self._entry


class EntryNotPresentAssertionError(ManifestCheckError):
    def __str__(self):
        return "Entry %s is present, but should not be" % self._entry


class EntryWrongTypeAssertionError(ManifestCheckError):
    def __str__(self):
        if self.actual is not None:
            return "Entry %s is supposed to be a %s but is a %s"  % (
                self.entry, self.expected, self.actual)
        return "Entry %s is present but not as %s" % (
            self.entry, self.expected)


class SymlinkTargetAssertionError(ManifestCheckError):
    def __str__(self):
        return "%s is a symlink but it is pointing to %s instead of %s" % (
            self.entry, self.actual, self.expected)


class EntryPermissionAssertionError(ManifestCheckError):
    def __str__(self):
        return "%s is mode 0%o instead of 0%o" % (self.entry, self.actual,
                                                  self.expected)
