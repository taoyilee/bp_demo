#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', 'numpy==1.18.1', 'matplotlib==3.1.3', 'scipy==1.4.1', 'bleak==0.5.1', 'screeninfo==0.6.3']

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="UCI cBP demo",
    author_email='taoyil@uci.edu',
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.8',
    ],
    description="GUI to demo continuous blood pressure sensing",
    entry_points={
        'console_scripts': [
            'uci_cbp_demo=uci_cbp_demo.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='uci_cbp_demo',
    name='uci_cbp_demo',
    packages=find_packages(include=['uci_cbp_demo', 'uci_cbp_demo.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/taoyilee/bp_demo',
    version='0.2',
    zip_safe=False,
)
