#!/usr/bin/env python

import re,string

from ReportConfig import ReportConfig

class ConfigParser:
    """
    Loads a configuration file, parses the contents, and returns the results as a ReportConfig object instance
    """

    def __init__(self,configFile):
        """
        Loads the configuration file
        """
        
        self.config = file(configFile).read()
        self.configuration = ReportConfig()
        
        
    def parseReport(self,reportName):
        """
        Parses the configuration file and returns a Report object
        according to the reportName.

        - reportName : the name of the report, tells which part of configuration file to use when making a ReportConfig

        returns 1 when there was a report with that name, 0 otherwise

        the access methods will probably fit here
        """
        
        reportRe = re.compile("^\s*"+reportName+"\s*\{(.*?)\}$",re.M|re.S|re.I)
        reResult = reportRe.search(self.config)
        
        if reResult:
            self.parseConfiguration(reResult.group(1))
            return 1
        else:
            return 0


    def parseConfiguration(self,reportConfiguration):
        """
        Parses the right portion of the configuration and builds a ReportConfig object, stone by stone.

        - reportConfiguration : the part of the configuration to build the configuration from

        """

        configurationRe = re.compile("^\s*\$(\S*)\s*\=\s*\"(.*?)\"\;?",re.M|re.S)
        reResult = configurationRe.findall(reportConfiguration)

        config = self.configuration

        for line in reResult:

            key = line[0]
            value = line[1]

            if key == "sql" or key == "query":
                config.setQuery(value)
            elif key == "overskrift" or key == "header":
                config.header = value
            elif key == "order_by" or key == "sort":
                config.orderBy = string.split(value,",") + config.orderBy
            elif key == "skjul" or key == "hidden" or key == "hide":
                config.hidden.extend(string.split(value,","))
            elif key == "ekstra" or key == "extra":
                config.extra.extend(string.split(value,","))
            elif key == "sum" or key == "total":
                config.sum.extend(string.split(value,","))
            else:
                reObject = re.compile("^(?P<group>\S+?)_(?P<groupkey>\S+?)$")
                reResult = reObject.search(key)

                if reResult:
                    if reResult.group('group') == "navn" or reResult.group('group') == "name":
                        config.name[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "url" or reResult.group('group') == "uri":
                        config.uri[reResult.group('groupkey')] = value
                    elif reResult.group('group') == "forklar" or reResult.group('group') == "explain" or reResult.group('group') == "description":
                        config.explain[reResult.group('groupkey')] = value

                else:
                    config.where.append(key + "=" + value)
