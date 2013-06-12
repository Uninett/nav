#!/usr/bin/python
"""Migrate rrd-files to whisper-files"""

import sys
import os
import rrdtool
import whisper
from collections import namedtuple
from operator import attrgetter
from optparse import OptionParser
from os.path import join, basename, exists, dirname


# pylint:disable=C0103
Period = namedtuple('Period', 'start_time end_time')
RRA = namedtuple('RRA', 'cf pdp_per_row rows')


def convert_to_whisper(rrd_file, metrics):
    """Convert a rrd-file to whisper"""

    print locals()

    rrd_info = rrdtool.info(rrd_file)
    seconds_per_point = rrd_info['step']
    last_update = rrd_info['last_update']

    rras = get_rras(rrd_info)
    retentions = calculate_retentions(rras, seconds_per_point)
    periods = calculate_time_periods(rras, seconds_per_point, last_update)

    for datasource in get_datasources(rrd_info):
        whisper_file = create_whisper_path(metrics[datasource])
        try:
            create_whisper_file(retentions, whisper_file)
        except whisper.InvalidConfiguration, err:
            print err
            continue

        datapoints = fetch_datapoints(rrd_file, periods, datasource)
        whisper.update_many(whisper_file, datapoints)
        print "%s created" % whisper_file


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


def calculate_time_periods(rras, seconds_per_point, last_update):
    """Calculates time periods from the rra definitions and step"""
    rras = sorted(rras, key=attrgetter('pdp_per_row'))
    periods = []
    last_start_time = last_update + seconds_per_point
    for rra in rras:
        rra_span = rra.pdp_per_row * rra.rows * seconds_per_point
        end_time = last_start_time
        last_start_time = start_time = (last_update - rra_span +
                                        seconds_per_point)
        periods.append(Period(start_time, end_time))

    return periods


def calculate_retentions(rras, seconds_per_point):
    """Creates retentions from the archive metadata"""
    retentions = []
    for rra in rras:
        precision = seconds_per_point * rra.pdp_per_row
        retentions.append((precision, rra.rows))
    return retentions


def get_datasources(rrd_info):
    """Gets the datasouces from the rrd-file"""
    ds_keys = [key for key in rrd_info if key.startswith('ds[')]
    datasources = list(set(key[3:].split(']')[0] for key in ds_keys))
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

        column_index = list(columns).index(datasource)
        rows.pop()  # The last value may be NaN based on when last update was
        values = [row[column_index] for row in rows]
        timestamps = list(range(*time_info))
        datapoints.extend(
            p for p in zip(timestamps, values) if p[1] is not None)

    return datapoints
