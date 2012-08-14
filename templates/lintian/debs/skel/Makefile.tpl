name = {{srcpkg}}

all: fix-perm
	create-deb -o $(name).deb control

clean:
	rm -f *.tar.gz *.deb md5sums debian-binary
	rm -rf root/

# If root/ exists, it is because the test ships with it.  Since the
# test may have been checked out (or unpacked) with a "whack umask"
# (anything but 0022), we reset the permissions to a reasonable
# default.
#
# The contents of the deb usually is not what is tested by this suite
# (t/tests is preferred for this), so the below merely handles the
# AVERAGE CASE.  Tests that need special permissions (anything but
# 0644 for files and 0755 for dirs) require manually setting the
# permissions.
fix-perm:
	[ ! -d root/ ] || (find root/ -type d | xargs chmod 0755 && \
			   find root/ -type f | xargs chmod 0644)
