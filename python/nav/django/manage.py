#!/usr/bin/env python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.."))
from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
