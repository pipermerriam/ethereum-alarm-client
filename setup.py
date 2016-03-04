#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from setuptools import setup, find_packages


DIR = os.path.dirname(os.path.abspath(__file__))


version = '7.0.0'

setup(
    name='ethereum-alarm-clock-client',
    version=version,
    description="""Ethereum Alarm Clock Client""",
    long_description="client for the ethereum-alarm-clock-service",
    author='Piper Merriam',
    author_email='pipermerriam@gmail.com',
    url='http://www.ethereum-alarm-clock.com',
    include_package_data=True,
    py_modules=['eth_alarm_client'],
    install_requires=[
        "populus>=0.7.2",
        "ethereum-rpc-client>=0.4.4",
        "ethereum-ipc-client>=0.1.9",
    ],
    license="MIT",
    zip_safe=False,
    keywords='ethereum',
    packages=find_packages(exclude=["tests", "tests.*"]),
    entry_points={
        'console_scripts': ["eth_alarm=eth_alarm_client.cli:main"],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
