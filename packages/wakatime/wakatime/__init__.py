# -*- coding: utf-8 -*-
"""
    wakatime
    ~~~~~~~~

    Action event appender for Wakati.Me, auto time tracking for text editors.

    :copyright: (c) 2013 Alan Hamlett.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function

__title__ = 'wakatime'
__version__ = '0.1.3'
__author__ = 'Alan Hamlett'
__license__ = 'BSD'
__copyright__ = 'Copyright 2013 Alan Hamlett'


import base64
import json
import logging
import os
import platform
import re
import sys
import time
import traceback
import urllib2

from .log import setup_logging
from .project import find_project
from .packages import argparse


log = logging.getLogger(__name__)


class FileAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        values = os.path.realpath(values)
        setattr(namespace, self.dest, values)


def parseArguments(argv):
    parser = argparse.ArgumentParser(
            description='Wakati.Me event api appender')
    parser.add_argument('--file', dest='targetFile', metavar='file',
            action=FileAction, required=True,
            help='absolute path to file for current action')
    parser.add_argument('--time', dest='timestamp', metavar='time',
            type=float,
            help='optional floating-point unix epoch timestamp; '+
                'uses current time by default')
    parser.add_argument('--endtime', dest='endtime',
            help='optional end timestamp turning this action into '+
                'a duration; if a non-duration action occurs within a '+
                'duration, the duration is ignored')
    parser.add_argument('--write', dest='isWrite',
            action='store_true',
            help='note action was triggered from writing to a file')
    parser.add_argument('--plugin', dest='plugin',
            help='optional text editor plugin name and version '+
                'for User-Agent header')
    parser.add_argument('--key', dest='key',
            help='your wakati.me api key; uses api_key from '+
                '~/.wakatime.conf by default')
    parser.add_argument('--logfile', dest='logfile',
            help='defaults to ~/.wakatime.log')
    parser.add_argument('--config', dest='config',
            help='defaults to ~/.wakatime.conf')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
            help='turns on debug messages in log file')
    parser.add_argument('--version', action='version', version=__version__)
    args = parser.parse_args(args=argv[1:])
    if not args.timestamp:
        args.timestamp = time.time()
    if not args.key:
        default_key = get_api_key(args.config)
        if default_key:
            args.key = default_key
        else:
            parser.error('Missing api key')
    return args


def get_api_key(configFile):
    if not configFile:
        configFile = '~/.wakatime.conf'
    api_key = None
    try:
        cf = open(os.path.expanduser(configFile))
        for line in cf:
            line = line.split('=', 1)
            if line[0] == 'api_key':
                api_key = line[1].strip()
        cf.close()
    except IOError:
        print('Error: Could not read from config file.')
    return api_key


def get_user_agent(plugin):
    user_agent = 'wakatime/%s (%s)' % (__version__, platform.platform())
    if plugin:
        user_agent = user_agent+' '+plugin
    return user_agent


def send_action(project=None, tags=None, key=None, targetFile=None,
        timestamp=None, endtime=None, isWrite=None, plugin=None, **kwargs):
    url = 'https://www.wakati.me/api/v1/actions'
    log.debug('Sending action to api at %s' % url)
    data = {
        'time': timestamp,
        'file': targetFile,
    }
    if endtime:
        data['endtime'] = endtime
    if isWrite:
        data['is_write'] = isWrite
    if project:
        data['project'] = project
    if tags:
        data['tags'] = list(set(tags))
    log.debug(data)
    request = urllib2.Request(url=url, data=json.dumps(data))
    user_agent = get_user_agent(plugin)
    request.add_header('User-Agent', user_agent)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Authorization', 'Basic %s' % base64.b64encode(key))
    response = None
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as exc:
        data = {
            'response_code': exc.getcode(),
            'response_content': exc.read(),
            sys.exc_info()[0].__name__: str(sys.exc_info()[1]),
        }
        if log.isEnabledFor(logging.DEBUG):
            data['traceback'] = traceback.format_exc()
        log.error(data)
    except:
        data = {
            sys.exc_info()[0].__name__: str(sys.exc_info()[1]),
        }
        if log.isEnabledFor(logging.DEBUG):
            data['traceback'] = traceback.format_exc()
        log.error(data)
    else:
        if response.getcode() >= 200 and response.getcode() < 300:
            log.debug({
                'response_code': response.getcode(),
                'response_content': response.read(),
            })
            return True
        log.error({
            'response_code': response.getcode(),
            'response_content': response.read(),
        })
    return False


def main(argv=None):
    if not argv:
        argv = sys.argv
    args = parseArguments(argv)
    setup_logging(args, __version__)
    if os.path.isfile(args.targetFile):
        project = find_project(args.targetFile)
        tags = project.tags()
        if send_action(project=project.name(), tags=tags, **vars(args)):
            return 0
        return 102
    else:
        log.debug('File does not exist; ignoring this action.')
    return 101
