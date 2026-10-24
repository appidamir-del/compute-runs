#!/bin/bash
# Lorenz H1 chunk: runs the standalone V4 script, outputs land in results/
set -e
export MPLBACKEND=Agg
pip install --quiet numpy scipy matplotlib tqdm
mkdir -p results
python3 tasks/lorenz-h1/lorenz.py
