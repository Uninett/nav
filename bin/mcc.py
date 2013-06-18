#!/usr/bin/env python
import ConfigParser
import logging
import time
from os.path import join
from subprocess import PIPE, Popen

from nav.path import localstatedir, sysconfdir
from nav.mcc.utils import start_config_creation
from nav.logs import init_file_logging

if __name__ == '__main__':
    init_file_logging(join(localstatedir, 'log/mcc.log'))

    # Read config
    config = ConfigParser.ConfigParser()
    config.read(join(sysconfdir, 'mcc.conf'))

    modulestring = config.get('mcc', 'modules')
    modules = [x.strip() for x in modulestring.split(',')]

    # Start logging
    logger = logging.getLogger('nav.mcc')

    logger.info("=============== Starting mcc ===============")
    starttime = time.time()

    # Start the collection modules
    start_config_creation(modules, config)

    # Compile cricket config
    logger.info("Compiling cricket database")
    try:
        # Run cricket-compile, get output from stderr
        output = Popen(['cricket-compile'], stderr=PIPE).communicate()[1]
        logger.debug("Output from cricket-compile\n%s" % output)
    except Exception:
        logger.error(
            "Could not run cricket-compile, make sure it is located in $PATH")

    endtime = time.time()
    timeused = endtime - starttime

    logger.info("Done. Time used: %.2f seconds"
                % timeused)
