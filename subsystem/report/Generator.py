#!/usr/bin/env python

import string
from urlparse import urlsplit
from ArgumentParser import ArgumentParser
from ConfigParser import ConfigParser
from DatabaseResult import DatabaseResult
from Report import Report

class Generator:
    """
    The maker and controller of the generating of a report
    """

    def __init__(self):

        self.config = None
        self.answer = None
    
    def makeReport(self,reportName,configFile,uri):
        """
        Makes a report

        - reportName : the name of the report that will be represented
        - configFile : the configuration file where the definittion resides
        - uri        : the request from the user as a uri

        returns a formatted report object instance
        """
        
        parsed_uri = urlsplit(uri)
        args = parsed_uri[3]
            
        configParser = ConfigParser(configFile)
        config = configParser.configuration
        parseOK = configParser.parseReport(reportName)

        if parseOK:
            argumentParser = ArgumentParser(config)
            argumentHash = argumentParser.parseArguments(args)
            argumentParser.parseQuery(argumentHash)

            answer = DatabaseResult(config)

            formatted = Report(config,answer,uri)
        
            return formatted

        else:

            return 0

