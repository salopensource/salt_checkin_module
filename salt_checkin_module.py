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


"""Copy salt returner results to sal report.

To avoid having no salt results to report due to timing, we write them
to a salt results file, which can then stick around even when sal cleans
up its report.
"""


import json
import pathlib

import sal


SALT_RETURNER_LOG = pathlib.Path('/usr/local/sal/salt_returner_results.json')


def main():
    results = {}
    if SALT_RETURNER_LOG.exists():
        try:
            results = json.loads(SALT_RETURNER_LOG.read_text())
        except ValueError:
            pass
    sal.set_checkin_results('Salt', results)


if __name__ == "__main__":
    main()