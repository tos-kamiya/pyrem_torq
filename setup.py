from distutils.core import setup

packages = [ 
    "pyrem_torq",
    "pyrem_torq.utility",
    "pyrem_torq.treeseq",
    "pyrem_torq.expression",
    "pyrem_torq.script",
    "pyrem_torq.extra"
]

setup(
    name = 'pyrem_torq',
    version = '0.5',
    packages = packages,
    package_dir = dict((p, "src/" + p.replace(".", "/")) for p in packages),
    package_data={'pyrem_torq': 
        [
            './LICENSE',
            './README.rst',
        ],
    },
    
    license="MIT license",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)

