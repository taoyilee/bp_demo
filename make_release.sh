#!/bin/bash
rm -rf build/lib build/nsis build/bdist.linux-x86_64 dist
pynsist installer.cfg
python setup.py bdist_wheel sdist
twine upload dist/*
