#!/usr/bin/python
# Copyright 2019 Shea G. Craig

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import datetime
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, '/usr/local/sal')
import utils


SALT_RETURNER_LOG = '/usr/local/sal/salt_returner_results.json'

LOG_PATTERN = (
    r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}\s*?'  # Date
    r'\[.*?\]'  # Junk
    r'\[(?P<message_type>WARNING|ERROR)\s*\]'  # LogLevel
    r'\[%s]\s*'  # We format the PID into this %s
    r'(?P<text>.*?(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}|$))')  # Match everything until
    # the next date or EOF.


def main():
    results = {}
    if os.path.exists(SALT_RETURNER_LOG):
        try:
            with open(SALT_RETURNER_LOG) as handle:
                results = json.load(handle)
        except ValueError:
            pass

    # Oddly, the rawfile_json returner puts the PID into the top level
    # dict. We grab it from Facts, since it's not in the normal log
    # output!
    results['messages'] = process_salt_logs(results['facts']['pid'])

    utils.set_checkin_results('Salt', results)


def process_salt_logs(pid):

    log_path = utils.pref('SALT_LOG_FILE', '/var/log/salt/minion')
    if os.path.exists(log_path):
        with open(log_path) as log_handle:
            log = log_handle.read()

    # Example log line:
    # 2019-03-06 10:01:23,094 [root             :384 ][WARNING ][6972] <THE MESSAGE>
    # The message could be just everything until \n, or it could be
    # multiple lines everything until \n, or it could be multiple lines
    # terminated by a double \n\n.

    # Format the PID into the regex we've prepared, and compile it.
    pattern = re.compile(LOG_PATTERN % pid, re.DOTALL)
    seen_matches = set()
    messages = []
    for match in re.finditer(pattern, log):
        if match.groups() not in seen_matches:
            messages.append(match.groupdict())
            seen_matches.add(match.groups())
    return messages


if __name__ == "__main__":
    main()
