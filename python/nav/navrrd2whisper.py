#!/usr/bin/python
"""Migrate rrd-files to whisper-files"""

import logging
import os
import rrdtool
import whisper
from collections import namedtuple
from datetime import datetime
from operator import attrgetter
from os.path import join, exists, dirname


# pylint:disable=C0103
Period = namedtuple('Period', 'start_time end_time step')
RRA = namedtuple('RRA', 'cf pdp_per_row rows')
Datasource = namedtuple('Datasource', 'name type')

_logger = logging.getLogger(__name__)


def convert_to_whisper(rrdfile, metrics, extra_retention=None):
    """Convert a rrd-file to whisper"""

    rrd_file = str(join(rrdfile.path, rrdfile.filename))
    try:
        rrd_info = rrdtool.info(rrd_file)
    except rrdtool.error, error:
        _logger.error(error)
    else:
        convert(rrd_file, rrd_info, metrics, extra_retention)


def convert(rrd_file, rrd_info, metrics, extra_retention=None):
    """Does the convertion from rrd to whisper"""
    seconds_per_point = rrd_info['step']
    last_update = rrd_info['last_update']
    rras = get_rras(rrd_info)
    retentions = calculate_retentions(rras, seconds_per_point)

    periods = calculate_time_periods(rras, seconds_per_point, last_update,
                                     extra_retention)

    # Add additional retention and period for special cases
    if extra_retention:
        retentions.insert(0, (extra_retention[0],
                              extra_retention[1] / extra_retention[0]))

    for datasource in get_datasources(rrd_info):
        whisper_file = create_whisper_path(metrics[datasource.name])
        try:
            create_whisper_file(retentions, whisper_file)
        except whisper.InvalidConfiguration, err:
            _logger.error(err)
            continue

        datapoints = fetch_datapoints(rrd_file, periods, datasource)
        whisper.update_many(whisper_file, datapoints)
        _logger.info('Created %s', whisper_file)


def get_rras(rrd_info):
    """Gets the archives metadata from the rrd-file"""
    rras = []
    rra_count = max(
        [int(key[4]) for key in rrd_info if key.startswith('rra[')]) + 1
    for i in range(rra_count):
        if rrd_info['rra[%d].cf' % i] == 'AVERAGE':
            rras.append(
                RRA(rrd_info['rra[%d].cf' % i],
                    rrd_info['rra[%d].pdp_per_row' % i],
                    rrd_info['rra[%d].rows' % i]))

    return rras


def calculate_retentions(rras, seconds_per_point):
    """Creates retentions from the archive metadata"""
    retentions = {}
    for rra in rras:
        precision = seconds_per_point * rra.pdp_per_row
        retentions[precision] = rra.rows
    return retentions.items()


def calculate_time_periods(rras, seconds_per_point, last_update,
                           extra_period=None):
    """Calculates time periods from the rra definitions and step"""
    rras = sorted(rras, key=attrgetter('pdp_per_row'))
    periods = []
    last_start_time = last_update + seconds_per_point
    if extra_period:
        periods.append(
            Period(last_start_time - extra_period[1],
                   last_start_time,
                   extra_period[0]))
    for rra in rras:
        rra_span = rra.pdp_per_row * rra.rows * seconds_per_point
        end_time = last_start_time
        last_start_time = start_time = (last_update - rra_span +
                                        seconds_per_point)
        periods.append(Period(start_time, end_time, None))

    return periods


def get_datasources(rrd_info):
    """Gets the datasouces from the rrd-file"""
    ds_keys = [key for key in rrd_info if key.startswith('ds[')]
    names = list(set(key[3:].split(']')[0] for key in ds_keys))
    datasources = []
    for name in names:
        datasources.append(Datasource(name, rrd_info['ds[%s].type' % name]))
    return datasources


def create_whisper_path(whisper_path):
    """Append correct filename extension for whisper files"""
    return whisper_path + '.wsp'


def create_whisper_file(retentions, whisper_file):
    """Create the whisper file with the correct retentions"""
    if dirname(whisper_file) and not exists(dirname(whisper_file)):
        os.makedirs(dirname(whisper_file))
    whisper.create(whisper_file, retentions)


def fetch_datapoints(rrd_file, periods, datasource):
    """Fetches the datapoints from the rrd-file"""
    datapoints = []
    for period in periods:
        (time_info, columns, rows) = rrdtool.fetch(
            rrd_file, 'AVERAGE',
            '-s', str(period.start_time),
            '-e', str(period.end_time))

        # rows.pop()  # The last value may be NaN based on when last update was
        column_index = list(columns).index(datasource.name)
        values = [row[column_index] for row in rows]
        if datasource.type in ['COUNTER', 'DERIVE']:
            values = calculate_absolute_from_rate(values, time_info[-1])

        timestamps = list(range(*time_info))

        if period.step and period.step < time_info[-1]:
            num_missing_values = time_info[-1] / period.step
            values = insert_missing_values(values, num_missing_values - 1)
            timestamps = list(range(time_info[0], time_info[1], period.step))

        datapoints.extend(
            p for p in zip(timestamps, values) if p[1] is not None)

    return datapoints


def insert_missing_values(values, num_missing_values):
    """Creates fake values to fill in between the values"""
    new_values = []
    for value in values:
        new_values.append(value)
        for _ in range(num_missing_values):
            new_values.append(value)

    return new_values


def calculate_absolute_from_rate(rates, interval):
    """Calculate the absolute values from the rates and interval"""
    last_value = 0
    values = []
    for rate in rates:
        if rate is None:
            values.append(None)
            last_value = 0
        else:
            value = (rate * interval) + last_value
            values.append(value)
            last_value = value
    return values
