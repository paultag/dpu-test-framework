import subprocess

def makefile_builder(workdir):
    subprocess.check_call(['make', '-C', workdir])

def dpkg_bpg_builder(workdir):
    subprocess.check_call(['dpkg-buildpackage'], cwd=workdir)

def noop_builder(workdir):
    pass

BUILDERS={
    'make': makefile_builder,
    'dpkg-buildpackage': dpkg_bpg_builder,
    'none': noop_builder,
    # XXX add plugin support or run "%(inc)/builder/%(builder)"
}

def run_builder(buildername, workdir):
    if buildername not in BUILDERS:
        raise ValueError("Unknown builder %s" % buildername)
    BUILDERS[buildername](workdir)

