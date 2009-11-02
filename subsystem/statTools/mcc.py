#!/usr/bin/env python
import ConfigParser
import logging
import time

from mcc.cricket import start_config_creation

if __name__ == '__main__':
    # TODO: Put logging to nav logging dir
    logging.basicConfig(level=logging.DEBUG,
                        filename='/tmp/mcc.log',
                        filemode='w',
                        format='%(asctime)s: %(name)s - %(message)s')

    config = ConfigParser.ConfigParser()
    # TODO: locate config file from nav's etc directory
    config.read('mcc.conf')

    modulestring = config.get('mcc', 'modules')
    modules = [x.strip() for x in modulestring.split(',')]

    logger = logging.getLogger('mcc')
    logger.info("Starting mcc")
    starttime = time.time()
    
    start_config_creation(modules, config)

    endtime = time.time()
    timeused = endtime - starttime

    logger.info("mcc done. Time used: %.2f seconds"
                %timeused)
