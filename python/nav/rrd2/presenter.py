#
# Copyright (C) 2012 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Abstraction of the rrd_file and rrd_datasource fields in the main NAV database.

Consists of three classes, presentation beeing the one of most interest to
other developers.

Quick example:

>>> import presenter
>>> a = presenter.Presentation() # instansiate presentation object
>>> a.add_datasource(454)        # Add rrd_datasourceid nr. 454 from
                                 # rrd_datasource table,
                                 # returns the default legend
'brev.stud - imap responsetime'
>>> a.time_last('week')          # We are interested in the data from a week
                                 # ago and until today
>>> a.average()
[0.0064152292421062644]          # imap responed with an average of 6milli..
                                 # hmm, whats the unit?
>>> a.units()
['s']                            # Ah. seconds, 6 ms then.
>>> a.add_datasource(427)        # Add another datasource
'brev.stud - pop3 responsetime'
>>> a.average()                  # It still works
[1.0, 0.0028113913067105887]
>>> a.title = 'My Graph'         # You can set the title to what you want
>>> a.graphUrl()
'http://isbre.itea.ntnu.no/rrd/rrdBrowser/graph?id=348552316'
                                 # Returns a link to an image representing
                                 # the two datasources. This link is valid
                                 # for about ten minutes
"""
import logging
import rrdtool
from nav.models.rrd import RrdDataSource


UNIT_MAP = {'s': 'Seconds',
            '%': 'Percent',
            '100%': 'Percent',
            }
_LOGGER = logging.getLogger(__name__)



# pylint: disable=W0201
class Presentation(object):
    """ Presentation class containing data sources

    can contain several data sources and helps to fetch
    average, sum, max ie from all your data sources """

    def __init__(self, time_frame='day', to_time='now', datasource=None):
        self.datasources = set()
        self.to_time = to_time
        self.none = None
        self.graph_height = 150
        self.graph_width = 500
        self.title = ''
        self.time_last(time_frame)
        self.time_frame = time_frame
        self.show_max = 0
        self.y_axis = 0

        if datasource:
            self.add_datasource(datasource)

    def units(self):
        """Returns the units of the rrd_datasources contained in the
        presentation object

        """
        units = []
        for i in self.datasources:
            units.append(i.units)
        return units

    def add_datasource(self, datasource):
        """Adds a datasource to the presentation, returns the default legend"""
        if type(datasource) == list:
            transaction = datasource
            try:
                [self.add_datasource(x) for x in datasource]
            except ValueError, error:
                _LOGGER.warning(error)

                [self.datasources.remove(remove_datasource) for
                 remove_datasource in transaction if
                 remove_datasource in self.datasources]

                raise error

        elif type(datasource) == RrdDataSource:
            self.datasources.add(datasource)

        else:
            raise ValueError(
                "must be a RrdDataSource or a list of RrdDataSource's")

        #return datasource.legend

    def fetch_valid(self):
        """Return the raw rrd-data as a list of dictionaries
        {'start':starttime in unixtime,
        'stop':stoptime in unixtime,
        'data':[data,as,list]}"""
        return_list = []
        for datasource in self.datasources:
            try:
                raw = rrdtool.fetch(str(datasource.rrd_file.get_file_path()),
                    'AVERAGE', '-s ' + str(self.from_time),
                    '-e ' + str(self.to_time))
                return_dict = {}
                return_dict['start'] = raw[0][0]
                return_dict['stop'] = raw[0][1]
                return_dict['deltaT'] = raw[0][2]

                row = list(raw[1]).index(datasource.name)
                invalid = 0
                data = []

                for i in raw[2]:
                    if type(i[row]) == type(None):
                        #                    data.append(self.none)
                        invalid += 1
                    else:
                        data.append(i[row])
                    return_dict['data'] = data
                    return_dict['invalid'] = invalid

            except rrdtool.error:
                return_dict = {}
                return_dict['start'] = ''
                return_dict['stop'] = ''
                return_dict['deltaT'] = ''
                return_dict['data'] = ''
                return_dict['invalid'] = ''
            return_list.append(return_dict)
        return return_list

    def sum(self):
        """Returns the sum of the valid  rrd-data"""
        sum_list = []
        data_list = self.fetch_valid()
        for data in data_list:
            sum = 0
            for i in data['data']:
                sum += i
            sum_list.append(sum)
        return sum_list

    def max(self):
        """Returns the local maxima of the valid rrd-data"""
        max_list = []
        for presentation in self.fetch_valid():
            data = presentation['data']
            if data:
                max_list.append(max(data))
            else:
                max_list.append(float('-nan'))
        return max_list

    def average(self, on_error_return=0, on_nan_return=0):
        """
        Returns the average of the valid rrd-data using rrdtool graph.

        onErrorReturn is the value appended to the returnlist if an
        error occured while fetching the value, default 0 (zero).

        onNanReturn is the value appended to the return list if a NaN
        value was the result of the average calculation, default=0
        (zero).
        """
        rrd_values = []
        rrd_start = str("-s %s" % self.from_time)
        rrd_end = str("-e %s" % self.to_time)

        for datasource in self.datasources:
            # The variablename (after def) is not important, it just
            # needs to be the same in the DEF and PRINT. We use
            # datasource.name.

            rrd_define = str("DEF:%s=%s:%s:AVERAGE" % (
                datasource.name,
                datasource.rrd_file.get_file_path(),
                datasource.name))
            rrd_print = str("PRINT:%s:AVERAGE:%%lf" % (datasource.name))

            try:
                # rrdtool.graph returns a tuple where the third
                # element is a list of values. We fetch only one
                # value, hence the rrd_tuple[2][0]
                rrd_tuple = rrdtool.graph('/dev/null', rrd_start, rrd_end,
                    rrd_define, rrd_print)
                rrd_value = rrd_tuple[2][0]
                # This works ok with nan aswell.
                real_value = float(rrd_value)
                if str(real_value) == 'nan':
                    rrd_values.append(on_nan_return)
                else:
                    rrd_values.append(real_value)
            except rrdtool.error:
                # We failed to fetch a value. Append onErrorReturn to
                # the list
                rrd_values.append(on_error_return)

        return rrd_values

    def min(self):
        """Returns the local minima of the valid rrd-data"""
        min_list = []
        for presentation in self.fetch_valid():
            data = presentation['data']
            if data:
                min_list.append(min(presentation['data']))
            else:
                min_list.append(float('-nan'))
        return min_list

    def valid_points(self):
        """Returns list of [number of points,number of invalid points,
        invalid/number of points]

        if first item is None, no valid data at all
        """

        valid = []
        raw_rrd_list = self.fetch_valid()
        for i in raw_rrd_list:
            data = i['data']
            if data:
                ret = [len(i['data'])]
                ret.append(i['data'].count(self.none))
                ret.append(ret[1] / float(ret[0]))
            else:
                ret = [None]

            valid.append(ret)
        return valid

    def time_last(self, time_frame='day', value=1):
        """Sets the timeframe of the presentation
        Currently valid timeframes: year,month,week,hour,day,minute"""

        if time_frame == 'year':
            self.from_time = '%s-%sY' % (self.to_time, value)
            self._time_frame = 'year'

        elif time_frame == 'month':
            self.from_time = '%s-%sm' % (self.to_time, value)
            self._time_frame = 'month'

        elif time_frame == 'week':
            self.from_time = '%s-%sw' % (self.to_time, value)
            self._time_frame = 'week'

        elif time_frame == 'day':
            self.from_time = '%s-%sd' % (self.to_time, value)
            self._time_frame = 'day'

        elif time_frame == 'hour':
            self.from_time = '%s-%sh' % (self.to_time, value)
            self._time_frame = 'hour'

        elif time_frame == 'day':
            self.from_time = '%s-%sd' % (self.to_time, value)
            self._time_frame = 'day'

        else:
            self.from_time = '%s-%smin' % (self.to_time, value)
            self._time_frame = 'minute'

    def remove_all_datasources(self):
        """Removes all datasources from the presentation object"""
        self.datasources = set()

    def remove_datasource(self, datasource):
        """Removes the datasource specified by rrd_datasourceid"""
        self.datasources.remove(datasource)

    # Yes we want to use the variable y
    # pylint: disable=C0103
    def set_y_axis(self, y):
        """ set y axis"""
        self.y_axis = y
