Source: {{source}}
Priority: {{priority}}
Section: {{section}}
Maintainer: {{maintainer}}
Standards-Version: {{standards_version}}
Build-Depends: debhelper (>= 7.0.50~)
Homepage: http://www.lintian.org/

Package: {{source}}
Architecture: {{architecture}}
Depends: ${shlibs:Depends}, ${misc:Depends}
Description: {{synopsis}}
 This is a test package designed to exercise some feature or tag of
 Lintian.  It is part of the Lintian test suite and may do very odd
 things.  It should not be installed like a regular package.  It may
 be an empty package.
