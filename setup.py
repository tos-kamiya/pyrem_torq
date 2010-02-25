from distutils.core import setup

packages = [ 
    "pytorqy",
    "pytorqy.utility",
    "pytorqy.treeseq",
    "pytorqy.expression",
    "pytorqy.expression_shortname",
    "pytorqy.compile",
    "pytorqy.operatorkit"
]

setup(
    name = 'pytorqy',
    version = '0.2',
    packages = packages,
    package_dir = dict((p, "src/" + p.replace(".", "/")) for p in packages)
)

