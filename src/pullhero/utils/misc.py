#!/usr/bin/env python3
# GNU GENERAL PUBLIC LICENSE
# Version 3, 29 June 2007
#
# Copyright (C) 2025 authors
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
import logging
import sys
import os
import json
import logging
import argparse
import requests
import sys
from gitingest import ingest
import pygit2

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

def get_banner():
    """
    Get banner method.

    This method prints
    pullhero's banner.
    """
    banner = """
:::::::::  :::    ::: :::        :::        :::    ::: :::::::::: :::::::::   ::::::::  
:+:    :+: :+:    :+: :+:        :+:        :+:    :+: :+:        :+:    :+: :+:    :+: 
+:+    +:+ +:+    +:+ +:+        +:+        +:+    +:+ +:+        +:+    +:+ +:+    +:+ 
+#++:++#+  +#+    +:+ +#+        +#+        +#++:++#++ +#++:++#   +#++:++#:  +#+    +:+ 
+#+        +#+    +#+ +#+        +#+        +#+    +#+ +#+        +#+    +#+ +#+    +#+ 
#+#        #+#    #+# #+#        #+#        #+#    #+# #+#        #+#    #+# #+#    #+# 
###         ########  ########## ########## ###    ### ########## ###    ###  ########  
"""
    return banner


def clone_repo_with_token(repo_url, local_path, github_token):
    """
    Clone the repository using the GITHUB_TOKEN for authentication with pygit2.
    """
    # Define the callback function for credentials (used by pygit2 for authentication)
    def credentials_callback(url, username_from_url, allowed_types):
        """
        Provide authentication credentials (username and password/token) for Git.
        """
        if github_token:
            return pygit2.UserPass("x-access-token", github_token)  # Use GitHub token for authentication
        else:
            raise ValueError("GITHUB_TOKEN is not set")

    try:
        # Perform the clone using pygit2 and pass the credentials callback for authentication
        logging.info(f"Cloning repository from {repo_url} to {local_path}")
        
        # Create a RemoteCallbacks object and pass it to pygit2
        remote_callbacks = pygit2.RemoteCallbacks(credentials=credentials_callback)
        
        # Set the callbacks to handle authentication
        pygit2.clone_repository(repo_url, local_path, callbacks=remote_callbacks)
        
        logging.info(f"Repository cloned to {local_path}")
    except Exception as e:
        logging.error(f"Error cloning the repository: {e}")
        raise



def call_ai_api(api_host, api_key, api_model, prompt):
    """Handles API calls with error handling."""
    url = f"https://{api_host}/v1/chat/completions"
    payload = {
        "model": api_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
