@echo off
python juicy.py -S . -B build
python juicy.py build -B build
.\build\Debug\hello