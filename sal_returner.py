import datetime
import os
import platform

import pytz
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


__virtualname__ = 'sal'
SAL_PATH = {'Darwin': '/usr/local/sal', None: None}.get(platform.system())


def __virtual__():
    if SAL_PATH:
        return __virtualname__
    return False, 'The sal_returner is not supported on this platform!'


def returner(ret):
    """"""
    results_path = os.path.join(SAL_PATH, 'salt_returner_results.json')

    results = {'managed_items': _process_managed_items(ret['return'])}
    results['facts'] = _flatten(_clean_grains(__grains__))

    # Replace the entire output every run.
    with open(results_path, 'w') as handle:
        salt.utils.json.dump(results, handle)


def _process_managed_items(items):
    # Salt's start_time is just a string representing local time, but
    # without offset. So combine today with the parsed time, and
    # localize to UTC before ISO formatting.
    today = datetime.date.today()
    utc = pytz.utc

    managed_items = {}
    for args, item in items.items():
        managed_item = {}
        managed_item['status'] = _get_status(args, item)
        # We have to make a datetime and then just drop the date, as
        # datetime.date strangely lacks the strptime func.
        time = datetime.datetime.strptime(item['start_time'], '%H:%M:%S.%f').time()
        managed_item['date_managed'] = utc.localize(
            datetime.datetime.combine(today, time)).isoformat()
        item.pop('start_time')

        item['args'] = args
        if item.get('changes'):
            item['changes'] = salt.utils.json.dumps(item['changes'])
        if item.get('pchanges'):
            item['pchanges'] = salt.utils.json.dumps(item['pchanges'])

        # Pop the ID off to use as a name for the Sal ManagedItem.
        item_id = item.pop('__id__')
        managed_item['data'] = item
        managed_items[item_id] = managed_item

    return managed_items


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

    else:
        result_dict[key] = source

    return result_dict


def _clean_grains(source):
    """Remove known problematic values from source."""
    source['productname'] = source['productname'].replace('\u0000', '')
    return source


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
        result = "UNKNOWN"
    return result