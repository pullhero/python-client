#!/usr/bin/env python3

import logging
import sys

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
