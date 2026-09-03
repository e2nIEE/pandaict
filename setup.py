#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: dheck
"""
import os
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirement_path = os.path.dirname(os.path.realpath(__file__)) + '/requirements.txt'
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = list(f.read().splitlines())

setuptools.setup(
    name="pandaict",
    version="1.2.1preview",
    author="Jan Ringelstein",
    author_email="jan.ringelstein@iee.fraunhofer.de",
    description="Toolbox for ICT networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.cc-asp.fraunhofer.de/recode/pandaict",
    project_urls={
        "Bug Tracker": "https://gitlab.cc-asp.fraunhofer.de/recode/pandaict/-/issues",
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=install_requires,
    include_package_data = True,
)
