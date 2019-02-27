#!/usr/bin/python


import datetime
import json
import os
import subprocess
import sys

sys.path.insert(0, '/usr/local/sal')
import utils


SALT_RETURNER_LOG = '/usr/local/sal/salt_returner_results.json'


def main():
    results = {}
    if os.path.exists(SALT_RETURNER_LOG):
        try:
            with open(SALT_RETURNER_LOG) as handle:
                results = json.load(handle)
        except ValueError:
            pass

    utils.set_checkin_results('salt', results)


if __name__ == "__main__":
    main()
