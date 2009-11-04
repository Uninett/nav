#!/usr/bin/env python
import ConfigParser
import logging
import time
from os.path import join
from subprocess import PIPE, Popen

from nav.path import localstatedir, sysconfdir
from nav.mcc.utils import start_config_creation

if __name__ == '__main__':
    # Create logger, log to nav's logdir
    logging.basicConfig(level=logging.DEBUG,
                        filename=join(localstatedir, 'log/mcc.log'),
                        filemode='w',
                        format='%(asctime)s: [%(levelname)s] %(name)s - %(message)s')

    # Read config
    config = ConfigParser.ConfigParser()
    config.read(join(sysconfdir, 'mcc.conf'))

    modulestring = config.get('mcc', 'modules')
    modules = [x.strip() for x in modulestring.split(',')]

    # Start logging, set loglevel
    logger = logging.getLogger('mcc')
    loglevel = config.get('mcc','loglevel')
    try:
        logger.setLevel(int(loglevel))
    except Exception:
        logger.setLevel(logging.getLevelName(loglevel.upper()))

    logger.info("Loglevel set to %s" %logger.getEffectiveLevel())

    logger.info("Starting mcc")
    starttime = time.time()

    # Start the collection modules
    start_config_creation(modules, config)

    # Compile cricket config
    logger.info("Compiling cricket database")
    try:
        # Run cricket-compile, get output from stderr
        output = Popen(['cricket-compile'], stderr=PIPE).communicate()[1]
        logger.debug("Output from cricket-compile\n%s" %output)
    except Exception:
        logger.error("Could not run cricket-compile, make sure it is located in $PATH")

    endtime = time.time()
    timeused = endtime - starttime

    logger.info("Done. Time used: %.2f seconds"
                %timeused)
