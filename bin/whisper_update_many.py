#!/usr/bin/env python
# -*- testargs: -h -*-
#
# Copyright (C) 2014, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Updates a whisper file with values from stdin

Based on
https://github.com/graphite-project/whisper/blob/master/bin/whisper-update.py

The license of this file is explicitly Apache License 2.0 in accordance with
this, and its usage of the whisper libraries. It is designed to be called
externally by NAV migration tools to avoid license incompatibilities between
GPL v2 and Apache License v2.

"""
import sys
import time
import argparse
try:
    import whisper
except ImportError:
    raise SystemExit('[ERROR] Please make sure whisper is installed properly')

now = int(time.time())
option_parser = argparse.ArgumentParser(
    description="Accepts multiple Whisper datapoints on stdin to update a "
                "single .wsp file"
)
option_parser.add_argument("filename", nargs=1,
                           help="path to a .wsp file to update")
args = option_parser.parse_args()

datapoint_strings = [point.replace('N:', '%d:' % now) for point in sys.stdin]
datapoints = [tuple(point.strip().split(':')) for point in datapoint_strings]

try:
    whisper.update_many(args.filename, datapoints)
except whisper.WhisperException as exc:
    raise SystemExit('[ERROR] %s' % str(exc))
