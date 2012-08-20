Source: {{source}}
Priority: {{priority}}
Section: {{section}}
Maintainer: {{maintainer}}
Standards-Version: {{standards_version}}
Build-Depends: debhelper {{debhelper.version}}
Homepage: http://www.lintian.org/
{% for bin in binaries %}
Package: {{bin.name}}
Architecture: {{bin.architecture}}
Depends: ${shlibs:Depends}, ${misc:Depends}{% if bin.deps %}{% for dep in bin.deps %}
 , {{dep}}{% endfor %}{% endif %}
Description: {{bin.synopsis}}
 This is a test package designed to exercise some feature or tag of
 Lintian.  It is part of the Lintian test suite and may do very odd
 things.  It should not be installed like a regular package.  It may
 be an empty package.
{% endfor %}
