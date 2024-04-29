#!/usr/bin/env python
from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

from nav.topology.detector import main

if __name__ == '__main__':
    main()
