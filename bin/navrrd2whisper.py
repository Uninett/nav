#!/usr/bin/python
"""Migrate rrd-files to whisper-files"""

import sys
import os
import rrdtool
import whisper
from collections import namedtuple
from operator import attrgetter
from optparse import OptionParser


# pylint:disable=C0103
Period = namedtuple('Period', 'start_time end_time')
RRA = namedtuple('RRA', 'cf pdp_per_row rows')


def main():
    """Controller"""
    args, options = get_optargs()

    rrd_path = args[0]
    rrd_info = rrdtool.info(rrd_path)
    seconds_per_point = rrd_info['step']
    last_update = rrd_info['last_update']

    rras = get_rras(rrd_info)
    retentions = calculate_retentions(rras, seconds_per_point)
    periods = calculate_time_periods(rras, seconds_per_point, last_update)
    datasources = get_datasources(rrd_info)

    for datasource in datasources:
        whisper_path = create_whisper_path(rrd_path, datasource)
        try:
            create_whisper_file(options, retentions, whisper_path)
        except whisper.InvalidConfiguration, err:
            print err
            continue

        datapoints = fetch_datapoints(datasource, periods, rrd_path)
        print ' migrating %d datapoints...' % len(datapoints)
        whisper.update_many(whisper_path, datapoints)


def get_optargs():
    """Get options and arguments from commandline"""
    option_parser = OptionParser(usage='''%prog rrd_path''')
    option_parser.add_option('--xFilesFactor', default=0.5, type='float')
    (options, args) = option_parser.parse_args()
    if len(args) < 1:
        option_parser.print_usage()
        sys.exit(1)
    return args, options


def get_rras(rrd_info):
    """Gets the archives metadata from the rrd-file"""
    rras = []
    rra_count = max(
        [int(key[4]) for key in rrd_info if key.startswith('rra[')]) + 1
    for i in range(rra_count):
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
        if rra.cf == 'AVERAGE':
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


def create_whisper_path(rrd_path, datasource):
    """Create whisper-path based on rrd-path and datasource"""
    return rrd_path.replace('.rrd', '_%s.wsp' % datasource)


def create_whisper_file(options, retentions, whisper_path):
    """Create the whisper file with the correct retentions"""
    whisper.create(whisper_path, retentions, xFilesFactor=options.xFilesFactor)
    size = os.stat(whisper_path).st_size
    print 'Created: %s (%d bytes)' % (whisper_path, size)


def fetch_datapoints(datasource, periods, rrd_path):
    """Fetches the datapoints from the rrd-file"""
    datapoints = []
    for period in periods:
        (time_info, columns, rows) = rrdtool.fetch(
            rrd_path, 'AVERAGE',
            '-s', str(period.start_time),
            '-e', str(period.end_time))

        column_index = list(columns).index(datasource)
        rows.pop()  # The last value may be NaN based on when last update was
        values = [row[column_index] for row in rows]
        timestamps = list(range(*time_info))
        datapoints.extend(
            p for p in zip(timestamps, values) if p[1] is not None)

    return datapoints


if __name__ == '__main__':
    main()
