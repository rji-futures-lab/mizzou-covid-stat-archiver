#!/bin/bash
# prepare a source code package

pip install --upgrade --target package/ -r requirements.txt
cd package
zip -r9 ${OLDPWD}/package.zip .
cd ${OLDPWD}
zip -g package.zip function.py

rm -rf package