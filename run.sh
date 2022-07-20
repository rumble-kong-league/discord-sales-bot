#!/bin/bash
# python needs to be poetry created environment
python main.py
while [ $? -ne 0 ]; do
    python main.py
done