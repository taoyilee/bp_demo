#!/bin/bash
rm -rf build
pynsist installer.cfg
python setup.py bdist_wheel sdist
twine upload dist/*
