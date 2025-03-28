#!/usr/bin/env python

"""
Copyright pullhero contributors.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
"""

from argparse import ArgumentParser
from pullhero.utils.get_banner import get_banner
from pkg_resources import get_distribution

pullhero_version = get_distribution('pullhero').version


def main():
    """
    Application's entry point.

    Here, application's settings are read from the command line,
    environment variables and CRD. Then, retrieving and processing
    of Kubernetes events are initiated.
    """
    parser = ArgumentParser(
        description='pullhero - CLI',
        prog='pullhero'
    )

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s ' + pullhero_version
    )

    parser.add_argument(
        '-b',
        '--banner',
        action='store_true',
        help="Print pullhero's banner"
    )

    args = parser.parse_args()

    # print("pullhero called with the folowing parameters")
    # print(parser.parse_args())

    if args.banner:
        print(get_banner())
        exit()
