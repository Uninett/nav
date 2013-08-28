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
from django.core.cache import cache

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
        self.from_time = time_last(self.to_time, time_frame)
        self.time_frame = time_frame
        self.none = None
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

    def add_datasource(self, datasources):
        """Adds a datasource to the presentation"""
        # TODO: check where this function is used, figure out if easily can
        # refactor to add   add_datasources function instead of this fugliness
        # without breaking existing code.

        if isinstance(datasources, RrdDataSource):
            datasources = [datasources]

        try:
            if not all(
                    [ds is not None and isinstance(ds, RrdDataSource) for ds in
                        datasources]):
                raise ValueError(
                    ("datasource or datasources "
                     "must be of instance RrdDataSource"))
        except TypeError: # Not iterable values, as single None and int.
                raise ValueError(
                    ("datasource or datasources "
                     "must be of instance RrdDataSource"))

        try:
            self.datasources.update(datasources)
        except ValueError, error:
            _LOGGER.warning(error)
            self.datasources.difference_update(datasources)
            raise error


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
        data_list = self.fetch_valid()
        sum_list = [sum(data['data']) for data in data_list]
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

    def remove_all_datasources(self):
        """Removes all datasources from the presentation object"""
        self.datasources = set()

    def remove_datasource(self, datasource):
        """Removes the datasource specified by rrd_datasourceid"""
        self.datasources.remove(datasource)


class Graph(object):
    """Represent an image of the data

    TODO: Add option for displaying values from other archives than AVERAGE
    """

    colorindex = 0
    color = {0: "#00cc00",
             1: "#0000ff",
             2: "#ff0000",
             3: "#00ffff",
             4: "#ff00ff",
             5: "#ffff00",
             6: "#cc0000",
             7: "#0000cc",
             8: "#0080C0",
             9: "#8080C0",
             10: "#FF0080",
             11: "#800080",
             12: "#0000A0",
             13: "#408080",
             14: "#808000",
             15: "#000000",
             16: "#00FF00",
             17: "#0080FF",
             18: "#FF8000",
             19: "#800000",
             20: "#FB31FB"}

    def __init__(self, title="", to_time="now", time_frame="day", opts=None,
                 args=None):
        """Add default options and parameters"""
        if not opts:
            opts = {}
        if not args:
            args = []

        from_time = time_last(to_time, time_frame)

        default_opts = {
            '-w': "500",
            '-h': "150",
            '-s': from_time,
            '-e': to_time,
            '-t': '%s' % title,
            '--no-minor': ''
        }

        self.opts = dict(default_opts.items() + opts.items())
        self.args = args

    def __repr__(self):
        return "Graph(%r, %r)" % (self.args, self.opts)

    def add_datasource(self, datasource, draw_as='LINE1', legend=None,
                       stack=False, consolidation='AVERAGE'):
        """Add a datasource to display in graph"""
        vname = self.add_def(datasource, consolidation)
        self.add_graph_element(vname, draw_as, legend, stack)
        return vname

    def add_argument(self, argument):
        """Add a argument to the graph"""
        self.args.append(argument)

    def add_option(self, option):
        """Add an option to the graph"""
        self.opts = dict(self.opts.items() + option.items())

    def add_def(self, datasource, consolidation='AVERAGE'):
        """Add a variable used for fetching data from a rrd-file

        The vname cannot be an integer as it may be used in a CDEF. Thus
        we prepend the string 'id' to the datasource id.

        To actually show something in the graph you need to use this def in a
        graph element.

        """
        vname = 'id' + str(datasource.id)
        defs = ['DEF',
                "%s=%s" % (vname, datasource.rrd_file.get_file_path()),
                datasource.name,
                consolidation]
        self.args.append(":".join(defs))
        return vname

    def add_cdef(self, cdefname, rpn):
        """Add a CDEF to the graph

        http://oss.oetiker.ch/rrdtool/tut/cdeftutorial.en.html

        """
        cdef = ['CDEF', "%s=%s" % (cdefname, rpn)]
        self.args.append(":".join(cdef))

    def add_graph_element(self, vname, draw_as="LINE1", legend="",
                          stack=False):
        """Add an element on the graph. """
        draw = [draw_as, "%s%s" % (vname, self._get_color())]
        if legend:
            draw.append(self._escape(legend))
        if stack:
            draw.append("STACK")
        self.args.append(":".join(draw))

    def _escape(self, string):
        return string.replace(':', '\:')

    def _get_color(self):
        color = self.color[self.colorindex]
        if self.colorindex == self.color.keys()[-1]:
            self.colorindex = 0
        else:
            self.colorindex += 1
        return color

    def get_url(self):
        """Return url for displaying graph"""
        cached_image = cache.get(repr(self))
        if cached_image:
            return cached_image

        try:
            image = rrdtool.graphv(*self._get_graph_args())['image']
        except rrdtool.error, error:
            _LOGGER.error(error)
        else:
            encoded_image = image.encode("base64").replace('\n', '')
            uri = 'data:image/png;base64,{0}'.format(encoded_image)
            cache.set(repr(self), uri)
            return uri

    def _get_graph_args(self):
        """Construct all arguments used to create the graph"""
        args = ['-']
        args.extend(["%s%s" % (x, y) for x, y in self.opts.items()])
        args.extend([str(s) for s in self.args])
        return args


def time_last(to_time, time_frame='day', value=1):
    """Return from_time based on time_frame and to_time
    Currently valid timeframes: year,month,week,hour,day,minute"""

    from_time = '%s-%smin' % (to_time, value)
    if time_frame == 'year':
        from_time = '%s-%sY' % (to_time, value)
    elif time_frame == 'month':
        from_time = '%s-%sm' % (to_time, value)
    elif time_frame == 'week':
        from_time = '%s-%sw' % (to_time, value)
    elif time_frame == 'day':
        from_time = '%s-%sd' % (to_time, value)
    elif time_frame == 'hour':
        from_time = '%s-%sh' % (to_time, value)
    elif time_frame == 'day':
        from_time = '%s-%sd' % (to_time, value)

    return from_time
