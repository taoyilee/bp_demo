#!/bin/bash
rm -rf build dist
pynsist installer.cfg
python setup.py bdist_wheel sdist
twine upload dist/*
