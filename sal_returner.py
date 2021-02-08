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
import os
import platform

import six

import salt.utils.json


PRESENT_FUNCS = (
    'cached',
    'directory',
    'enabled',
    'exists',
    'installed',
    'managed',
    'present',
    'running',)
ABSENT_FUNCS = (
    'absent',
    'dead',
    'disabled',
    'removed',)

__version__ = '0.2.3'
__virtualname__ = 'sal'
SAL_PATH = {'Darwin': '/usr/local/sal', None: None}.get(platform.system())
RESULTS_PATH = '/usr/local/sal/salt_returner_results.json'


def __virtual__():
    if SAL_PATH:
        return __virtualname__
    return False, 'The sal_returner is not supported on this platform!'


def returner(ret):
    """"""
    results_path = os.path.join(SAL_PATH, 'salt_returner_results.json')
    results = {}
    try:
        results['managed_items'], results['messages'] = _process_managed_items(ret['return'])
        results['extra_data'] = _process_extra_data(ret)
        results['facts'] = _flatten(_clean_grains(__grains__))
        results['facts']['Last Highstate'] = datetime.datetime.now(
            datetime.timezone.utc).isoformat()

    except Exception as error:
        messages = results.get("messages", [])
        messages.append(f"Sal returner crashed with error: {error}")
        results["messages"] = messages

    _save_results(results)


def _process_managed_items(items):
    # Handle errors that prevent Salt from running; probably state
    # compilation failures.
    if isinstance(items, list):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return {}, [{"text": m, "message_type": "ERROR", "date": now} for m in items]

    # Salt's start_time is just a string representing local time, but
    # without offset. So combine today with the parsed time, and
    # localize to UTC before ISO formatting.
    today = datetime.date.today()

    managed_items = {}
    messages = []

    for args, item in items.items():
        if '__id__' not in item:
            # This is a state that was not run due to the requisite
            # system. Skip it.
            continue
        managed_item = {}
        managed_item['status'] = _get_status(args, item)
        # We have to make a datetime and then just drop the date, as
        # datetime.date strangely lacks the strptime func.
        time = datetime.datetime.strptime(item['start_time'], '%H:%M:%S.%f').time()
        managed_time = pytz.utc.localize(
            datetime.datetime.combine(today, time)).isoformat()
        managed_item['date_managed'] = managed_time
        item.pop('start_time')

        # Add a message if the state failed.
        if not item['result']:
            messages.append(
                {'text': item['comment'], 'message_type': 'ERROR', 'date': managed_time})

        item['args'] = args
        if item.get('changes'):
            item['changes'] = salt.utils.json.dumps(item['changes'])
        if item.get('pchanges'):
            item['pchanges'] = salt.utils.json.dumps(item['pchanges'])

        # Pop the ID off to use as a name for the Sal ManagedItem.
        item_id = item.pop('__id__')
        managed_item['data'] = item
        managed_items[item_id] = managed_item

    return managed_items, messages


def _process_extra_data(ret):
    extra_data = {
        'jid': ret['jid'],
        'success': ret['success'],
        'retcode': ret.get(
            'retcode', 'Sal returner did not get a retcode! Please investigate.'),
    }
    return extra_data


def _flatten(source, key=None):
    """Flattens a dicts values into str for submission

    Args:
        source (dict): Data to flatten, with potentially nonhomogeneous
            value types (specifically, container types).

    Returns:
        Dict with all values as single objects.
    """
    result_dict = {}

    if isinstance(source, dict):
        for k, v in source.items():
            if key:
                recurse_key = '{}=>{}'.format(key, k)
            else:
                recurse_key = k
            result_dict.update(_flatten(v, key=recurse_key))

    elif isinstance(source, (list, tuple)):
        if all(isinstance(i, (int, float, str)) for i in source):
            result_dict[key] = ", ".join(str(i) for i in source)
        else:
            for index, value in enumerate(source):
                result_dict.update(_flatten(value, key='{}=>{}'.format(key, index)))

    elif source is None:
        source = ""

    else:
        result_dict[key] = source

    return result_dict


def _clean_grains(source):
    """Remove known problematic values from source."""
    # The productname and model sometimes has some null characters.
    pattern = '\u0000' if six.PY3 else '\x00'
    str_type = str if six.PY3 else unicode
    return {k: v.replace(pattern, '') if isinstance(v, str_type) else v for k, v in source.items()}


def _get_status(args, item):
    """Return a Sal ManagedItem status based on the salt module results

    First looks at the result value; False is always an ERROR.

    Then, uses a table to look up Present/Absent against known state
    modules actions used in the args. E.g.
    'schedule_|-Schedule tarball update_|-tarball_update_|-present'
    is PRESENT.

    Args:
        args (str): Salt results key.
        item: A single entry from the salt results.

    Returns:
        Sal ManagedItem.status value.
    """
    func = args.split('|')[-1][1:]
    if not item['result']:
        result = 'ERROR'
    elif func in PRESENT_FUNCS:
        result = "PRESENT"
    elif func in ABSENT_FUNCS:
        result = "ABSENT"
    else:
        # As we iterate on the Sal managed item statuses, just assume
        # that if it isn't an error, and not an "ABSENT", that it is
        # successful and should be considered "PRESENT" for lack of
        # something more accurate; e.g. longterm it will probably be
        # either whatever str you want to use for status, or something
        # more indicative of desired state; Okay/Error/Pending/Changed?
        result = "PRESENT"
    return result


def _save_results(data):
    """Replace all data in the results file."""
    with open(RESULTS_PATH, 'w') as results_handle:
        salt.utils.json.dump(data, results_handle)
