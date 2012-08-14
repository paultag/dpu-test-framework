import os

from dpu.util import disposabledir
from dpu.template import copy_template_dir


targetdir = "./tests/staging/test-skeleton"
upstream = "./tests/resources/skeletons/upstream"
debian =  "./tests/resources/skeletons/debian"

def test_copy_template_dir():
    with disposabledir(targetdir):
        copy_template_dir(upstream, debian, targetdir,
                          exclude_skel=["upstream-excluded"],
                          exclude_test_src=["debian-excluded"])
        for f in ("in-both", "in-upstream", "in-debian"):
            assert os.path.isfile("%s/%s" % (targetdir, f))

        for nf in ("upstream-excluded", "debian-excluded"):
            assert not os.path.exists("%s/%s" % (targetdir, nf))

        with open("%s/in-both" % targetdir) as f:
            assert f.read().strip() == "debian"
