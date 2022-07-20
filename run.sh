#!/bin/bash
# python needs to be poetry created environment
python -m src.main $1
while [ $? -ne 0 ]; do
    python -m src.main $1
done