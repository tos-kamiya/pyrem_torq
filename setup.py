from distutils.core import setup

packages = [ 
    "pyrem_torq",
    "pyrem_torq.utility",
    "pyrem_torq.treeseq",
    "pyrem_torq.expression",
    "pyrem_torq.compile",
    "pyrem_torq.helper"
]

setup(
    name = 'pyrem_torq',
    version = '0.2',
    packages = packages,
    package_dir = dict((p, "src/" + p.replace(".", "/")) for p in packages)
)

