#!/usr/local/sal/Python.framework/Versions/3.8/bin/python3
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
import pathlib
import re

import sal


SALT_RETURNER_LOG = pathlib.Path('/usr/local/sal/salt_returner_results.json')
# This is the default time format; if you have configured your Salt
# install to use something else, you'll need to edit the TIME_FORMAT and
# LOG_PATTERN below to parse it correctly.
TIME_FORMAT = '%Y-%m-%d %H:%M:%S,%f'
LOG_PATTERN = (
    r'(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s*?'  # Date
    r'\[.*?\]'  # Junk
    r'\[(?P<message_type>WARNING|ERROR)\s*\]'  # LogLevel
    r'\[%s]\s*'  # We format the PID into this %s
    r'(?P<text>.*?(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}|$))')  # Match everything until
    # the next date or EOF.


def main():
    results = {}
    if SALT_RETURNER_LOG.exists():
        try:
            results = json.loads(SALT_RETURNER_LOG.read_text())
        except ValueError:
            pass

    # Oddly, the returner puts the PID into the top level
    # dict. We grab it from Facts, since it's not in the normal log
    # output!
    if 'facts' in results and 'pid' in results['facts']:
        results['messages'] = process_salt_logs(results['facts']['pid'])

    sal.set_checkin_results('Salt', results)


def process_salt_logs(pid):

    log_path = pathlib.Path(sal.pref('SALT_LOG_FILE', '/var/log/salt/minion'))
    if log_path.exists():
        log = log_path.read_text()
    else:
        log = ''

    # Example log line:
    # 2019-03-06 10:01:23,094 [root             :384 ][WARNING ][6972] <THE MESSAGE>
    # The message could be just everything until \n, or it could be
    # multiple lines terminated by a double \n\n.

    # Format the PID into the regex we've prepared, and compile it.
    pattern = re.compile(LOG_PATTERN % pid, re.DOTALL)
    # TODO: See below.
    # seen_matches = set()
    messages = []
    for match in pattern.finditer(log):
        message = match.groupdict()
        # Grab the log datetime; this has no TZ offset, so we convert to
        # UTC before serializing.
        date = datetime.datetime.strptime(message['date'], TIME_FORMAT).astimezone(
            datetime.timezone.utc).isoformat()
        message['date'] = date
        messages.append(message)
        # TODO: This commented out code was in place to filter
        # potentially massively redundant messages. Not sure we want
        # this though, so leaving it in as an item of consideration for
        # future releases.

        # Filter out duplicate messages
        # if message not in seen_matches:
            # seen_matches.add(match.groups())
    return messages


if __name__ == "__main__":
    main()
