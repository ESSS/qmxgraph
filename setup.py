# DUMMY CHANGE
# DUMMY CHANGE 2
# DUMMY CHANGE 2 used to test err-stash, do not merge this.
# DUMMY CHANGE 3
# DUMMY CHANGE 4
# DUMMY CHANGE 5
# DUMMY CHANGE 6
# DUMMY CHANGE 7
# DUMMY CHANGE 8

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup(
    name='qmxgraph',
    version='0.1.0',
    description="A Qt graph drawing widget using JavaScript's mxGraph "
                "library.",
    long_description=readme + '\n\n' + history,
    author="Rafael Bertoldi",
    author_email='tochaman@gmail.com',
    url='https://github.com/ESSS/qmxgraph',
    packages=[
        'qmxgraph',
    ],
    package_dir={'qmxgraph':
                 'qmxgraph'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='qmxgraph',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: User Interfaces',
    ],
    test_suite='tests',
    tests_require=[],
)
