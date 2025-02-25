#!/bin/bash
set -e

# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007
#
# Copyright (C) 2025 Carlos Camacho and authors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

# Make sure .bashrc is sourced
. /root/.bashrc

export GITHUB_TOKEN=$1
export LLM_API_KEY=$2
export LLM_API_HOST=$3
export LLM_API_MODEL=$4
export LLM_MODEL_DIGEST_LENGTH=$5

echo "Run pullhero"
python /usr/bin/pullhero.py
