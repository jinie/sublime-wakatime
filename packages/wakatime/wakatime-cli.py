# -*- coding: utf-8 -*-
"""
    wakatime-cli
    ~~~~~~~~~~~~

    Action event appender for Wakati.Me, auto time tracking for text editors.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function

import sys
import wakatime

if __name__ == '__main__':
    sys.exit(wakatime.main(sys.argv))