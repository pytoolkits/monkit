#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "monkit",
    version = "0.0.5",
    keywords = ["monurl", "monitor", "monkit"],
    description = "monitor kit client",
    long_description = "monitor kit client",
    license = "MIT Licence",

    url = "https://github.com/pytoolkits/monkit",
    author = "hhr66",
    author_email = "hhr66@qq.com",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = [],
    scripts = [],
    entry_points = {
        'console_scripts': [
            'monurl = monkit.monurl:main'
        ]
    }
)
