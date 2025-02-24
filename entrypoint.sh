#!/bin/bash
set -e

# Make sure .bashrc is sourced
. /root/.bashrc

export LLM_API_KEY=$1
export GITHUB_TOKEN=$2
export GITHUB_EVENT_PATH=$3

python ./pullhero.py
