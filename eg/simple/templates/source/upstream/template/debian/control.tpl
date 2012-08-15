Source: {{src_pkg}}
Priority: {{priority}}
Section: {{section}}
Maintainer: {{maintainer}}
Standards-Version: {{standards_version}}
Build-Depends: debhelper {{debhelper.version}}
Homepage: http://www.lintian.org/
{% for pkg in bin_pkgs %}
Package: {{pkg.name}}
Architecture: {{pkg.architecture}}
Depends: ${shlibs:Depends}, ${misc:Depends}
Description: {{pkg.synopsis}}
 This is a test package designed to exercise some feature or tag of
 Lintian.  It is part of the Lintian test suite and may do very odd
 things.  It should not be installed like a regular package.  It may
 be an empty package.
{% endfor %}
