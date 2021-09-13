#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = []

setup(
    name='qmxgraph',
    version='0.1.0',
    description="A Qt graph drawing widget using JavaScript's mxGraph " "library.",
    long_description=readme + '\n\n' + history,
    author="Rafael Bertoldi",
    author_email='tochaman@gmail.com',
    url='https://github.com/ESSS/qmxgraph',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: User Interfaces',
    ],
    test_suite='tests',
    tests_require=[],
)
