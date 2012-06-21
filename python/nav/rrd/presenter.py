#
# Copyright (C) 2003 Norwegian University of Science and Technology
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

CONFIG_FILE = 'rrdviewer/rrdviewer.conf'
import nav.db
import nav.config
import time
import rrdtool
import random
import glob
import os
from os import path
import psycopg2.extras

UNIT_MAP = {'s': 'Seconds',
            '%': 'Percent',
            '100%': 'Percent',
            }

# ignore class has too few public methods
# pylint: disable=R0903


class RrdFile:
    """Class representing an RRD file"""

    def __init__(self, rrd_fileid):
        cursor = nav.db.getConnection('rrdpresenter').cursor(
            cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("select * from rrd_file natural join netbox "
                       "where rrd_fileid=%s" % rrd_fileid)
        result = cursor.fetchone()
        self.path = result['path']
        self.filename = result['filename']
        self.netboxid = result['netboxid']
        self.key = result['key']
        self.value = result['value']
        self.subsystem = result['subsystem']
        self.sysname = result['sysname']

    def full_path(self):
        """ Retreives full file system path for the RRD file
        """
        rrd_file_path = path.join(self.path, self.filename)
        return rrd_file_path


class DataSource:
    """ Class representing a datasource.

    Can perform simple calculations on the datasource """

    # ignore class has too many instance attributes
    # pylint: disable=R0902

    def __init__(self, rrd_datasourceid, linetype='LINE2'):
        cursor = nav.db.getConnection('rrdpresenter').cursor(
            cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("select * from rrd_datasource "
                       "where rrd_datasourceid=%s" % rrd_datasourceid)
        result = cursor.fetchone()
        self.name = result['name']
        self.description = result['descr']
        self.datasource_type = result['dstype']
        self.units = result['units']
        self.rrd_datasourceid = result['rrd_datasourceid']
        self.linetype = linetype
        self.rrd_fileobj = RrdFile(result['rrd_fileid'])
        self.sysname = self.rrd_fileobj.sysname
        self.legend = '%s - %s' % (self.rrd_fileobj.sysname, self.description)
        cursor.close()

    def get_id(self):
        """Retrieves the data source id"""
        return self.rrd_datasourceid

    def __eq__(self, obj):
        return obj.rrd_datasourceid == self.rrd_datasourceid

    def __str__(self):
        return "%s - %s" % (self.name, self.description)

    def __repr__(self):
        return "%s - %s" % (self.name, self.description)

    def full_path(self):
        """ Retreives full file system path for RRD file associated with
        Datasource
        """
        return self.rrd_fileobj.full_path()


# pylint: disable=W0201
class Presentation:
    """ Presentation class containing data sources

    can contain several data sources and helps to fetch
    average, sum, max ie from all your data sources """

    def __init__(self, time_frame='day', datasource=''):
        self.datasources = []
        self.none = None
        self.graph_height = 150
        self.graph_width = 500
        self.title = ''
        self.time_last(time_frame)
        self.time_frame = time_frame
        self.show_max = 0
        self.y_axis = 0
        if datasource != '':
            self.add_datasource(datasource)

    # pylint: disable=W0622
    def serialize(self):
        """Serializes Presentation class to a dict"""
        repr = {}
        repr['datasources'] = []
        for datasource in self.datasources:
            repr['datasources'].append(datasource.get_id())
        repr['timeframe'] = self.time_frame
        return repr

    def units(self):
        """Returns the units of the rrd_datasources contained in the
        presentation object

        """
        units = []
        for i in self.datasources:
            units.append(i.units)
        return units

    def add_datasource(self, datasource_id):
        """Adds a datasource to the presentation, returns the default legend"""
        datasource = DataSource(datasource_id)
        self.datasources.append(datasource)
        return datasource.legend

    def __str__(self):
        return str(self.datasources)

    def __repr__(self):
        return str(self.datasources)

    def fetch_valid(self):
        """Return the raw rrd-data as a list of dictionaries
        {'start':starttime in unixtime,
        'stop':stoptime in unixtime,
        'data':[data,as,list]}"""
        return_list = []
        for datasource in self.datasources:
            try:
                raw = rrdtool.fetch(str(datasource.full_path()),
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
            max_list.append(max(presentation['data']))
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
                datasource.full_path(),
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
            min_list.append(min(presentation['data']))
        return min_list

    def valid_points(self):
        """Returns list of [number of points,number of invalid points,
        invalid/number of points]

        """
        valid = []
        raw_rrd_list = self.fetch_valid()
        for i in raw_rrd_list:
            ret = [len(i['data'])]
            ret.append(i['data'].count(self.none))
            ret.append(ret[1] / float(ret[0]))
            valid.append(ret)
        return valid

    def time_last(self, time_frame='day', value=1):
        """Sets the timeframe of the presentation
        Currently valid timeframes: year,month,week,hour,day,minute"""
        self.to_time = 'now'
        if time_frame == 'year':
            self.from_time = 'now-%sY' % value
            self._time_frame = 'year'

        elif time_frame == 'month':
            self.from_time = 'now-%sm' % value
            self._time_frame = 'month'

        elif time_frame == 'week':
            self.from_time = 'now-%sw' % value
            self._time_frame = 'week'

        elif time_frame == 'day':
            self.from_time = 'now-%sd' % value
            self._time_frame = 'day'

        elif time_frame == 'hour':
            self.from_time = 'now-%sh' % value
            self._time_frame = 'hour'

        elif time_frame == 'day':
            self.from_time = 'now-%sd' % value
            self._time_frame = 'day'

        else:
            self.from_time = 'now-%smin' % value
            self._time_frame = 'minute'

    def remove_all_datasources(self):
        """Removes all datasources from the presentation object"""
        self.datasources = []

    def remove_datasource(self, datasource_id):
        """Removes the datasource specified by rrd_datasourceid"""
        datasource = DataSource(datasource_id)
        self.datasources.remove(datasource)

    # Yes we want to use the variable y
    # pylint: disable=C0103
    def set_y_axis(self, y):
        """ set y axis"""
        self.y_axis = y

    def graph_url(self):
        """Generates an url to a image representing the current presentation"""
        url = 'graph.py'
        index = 0
        params = ['-w' + str(self.graph_width),
                  '-h' + str(self.graph_height),
                  '-s' + self.from_time,
                  '-e' + self.to_time,
                  '--no-minor',
                  ]
        try:
            params.append('-t %s' % self.title)
        except NameError:
            pass

        if self.y_axis:
            params.append('--rigid')  # Rigid boundry mode
            params.append('--upper-limit')
            params.append(str(self.y_axis))  # allows 'zooming'
        units = []

        for datasource in self.datasources:
            color_max = {0: '#6b69e1',
                         1: '#007F00',
                         2: '#7F0000',
                         3: '#007F7F',
                         4: '#7F7F00',
                         5: '#7F007F',
                         6: '#000022',
                         7: '#002200',
                         8: '#220000'}

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

            #color = {0:'#0F0CFF',
            #         1:'#00FF00',
            #         2:'#FF0000',
            #         3:'#00FFFF',
            #         4:'#FFFF00',
            #         5:'#FF00FF',
            #         6:'#000044',
            #         7:'#004400',
            #         8:'#440000'}
            rrd_variable = 'avg' + str(index)
            rrd_max_variable = 'max' + str(index)
            rrd_filename = datasource.full_path()
            rrd_datasourcename = datasource.name
            linetype = datasource.linetype
            linetype_max = 'LINE1'
            legend = datasource.legend
            if datasource.units and datasource.units.count("%"):
                # limit to [0,100]
                params += ['--upper-limit', '100', '--lower-limit', '0']
            params += ['DEF:' + rrd_variable + '=' + rrd_filename + ':' +
                       rrd_datasourcename + ':AVERAGE']
            # Define virtuals to possibly do some percentage magical
            # flipping
            virtual = 'CDEF:v_' + rrd_variable + '='
            if datasource.units and datasource.units.startswith('-'):
                # availability is flipped up-side down, revert
                # and show as percentage
                virtual += '1,%s,-' % rrd_variable
                units.append(datasource.units[1:])
            else:
                if datasource.units:
                    units.append(datasource.units)
                virtual += rrd_variable
            if datasource.units and datasource.units.endswith("%"):
                # percent, check if we have to do some scaling...
                scaling_factor = datasource.units[:-1]  # strip %
                if scaling_factor.startswith('-'):
                    scaling_factor = scaling_factor[1:]
                try:
                    int(scaling_factor)
                    virtual += ',100,*'
                except ValueError:
                    pass

            params += [virtual]
            params += [linetype + ':v_' + rrd_variable +
                       color[index % len(color)] + ':' + '' + legend + '']

            a = rrdtool.info(str(rrd_filename))
            # HVA I HELVETE SKJER HER!?!?!??!?!
            if (self.show_max and
                'MAX' in [a.get('rra')[i].get('cf')
                          for i in range(len(a.get('rra')))]):
                legend += ' - MAX'
                params += ['DEF:' + rrd_max_variable + '=' + rrd_filename +
                           ':' + rrd_datasourcename + ':MAX']
                virtual = 'CDEF:v_' + rrd_max_variable + '='
                if datasource.units and datasource.units.startswith('-'):
                    # begins with -
                    # availability is flipped up-side down, revert
                    # and show as percentage
                    virtual += '1,%s,-' % rrd_max_variable
                else:
                    virtual += rrd_max_variable

                if datasource.units and datasource.units.endswith("%"):
                    # percent, check if we have to do some scaling...
                    scaling_factor = datasource.units[:-1]  # strip %
                    if scaling_factor.startswith('-'):
                        scaling_factor = scaling_factor[1:]
                    try:
                        int(scaling_factor)
                        virtual += ',100,*'
                    except ValueError:
                        pass

                params += [virtual]
                params += [linetype_max + ':v_' + rrd_max_variable +
                           color_max[index] + ':' + '' + legend + '']

            index += 1

        if index == 0:
            params += ["COMMENT:''"]
        if units:
            params.insert(0, '-v')

            def uniq(list):
                """Join together with / if there is several different units"""
                a = {}
                return [x for x in list
                        if not a.has_key(x) and a.setdefault(x, True)]

            units = uniq(units)
            unit_strings = []
            for unit in units:
                unit_strings.append(UNIT_MAP.get(unit, unit))
            params.insert(1, '/'.join(unit_strings))
        id = self.generate_image(*params)
        return '/rrd/image=%s/' % str(id)

    # ignore no exception type(s) specified
    # pylint: disable=W0702
    def generate_image(self, *rrd_params):
        """ generates a image using rrdtool of given data sources in
         a Presenter() instance
        """
        config = nav.config.readConfig(CONFIG_FILE)
        id = str(random.randint(1, 10 ** 9))
        image_filename = config['file_prefix'] + id + config['file_suffix']
        rrd_params = (image_filename,) + rrd_params
        try:
            size = rrdtool.graph(*[str(s) for s in rrd_params])
        except rrdtool.error:
            pass
        deadline = 60 * 10
        for i in glob.glob(config['file_prefix'] + '*'):
            if os.path.getmtime(i) < (time.time() - deadline):
                try:
                    os.unlink(i)
                except:
                    pass
        return id


# pylint: disable=W0622
class Page:
    """Page represents multiple Presentation's"""

    def __init__(self, repr=None):
        """
        repr must be a dict as created by serialize()
        """
        self.presentations = []
        self.time_frame = "day"
        self.name = ''
        self.time_frame_index = 1
        if repr:
            self.de_serialize(repr)

    def de_serialize(self, repr):
        """De serializes a Page in dict format"""
        if type(repr) != dict:
            return
        presentations = repr['presentations']
        self.time_frame = repr['timeframe']
        for presentation in presentations:
            new_presentation = Presentation(time_frame=self.time_frame)
            for datasource in presentation['datasources']:
                new_presentation.add_datasource(datasource)
            self.presentations.append(new_presentation)

    def serialize(self):
        """Serializes a Page in dict format"""
        repr = {}
        repr['presentations'] = []
        for i in self.presentations:
            repr['presentations'].append(i.serialize())
        repr['timeframe'] = self.time_frame
        repr['name'] = self.name
        return repr

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def graph(request, id):
    """ Renders a graph request from mod_python
    :param id id of stored graph to render
    """
    config = nav.config.readConfig(CONFIG_FILE)
    filename = config['file_prefix'] + id + config['file_suffix']
    request.content_type = 'image/gif'
    request.send_http_header()
    file = open(filename)
    request.write(file.read())
    file.close()
