from __future__ import print_function

import contextlib
import importlib
import logging
import os
import sys
import re
import colorama

import yaml
from distutils.version import LooseVersion
from ansible.module_utils.parsing.convert_bool import boolean as to_bool

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

def count_spaces(c_string):
    leading_spaces = 0
    trailing_spaces = 0

    for i, e in enumerate(c_string):
        if not e.isspace():
            break
        leading_spaces += 1

    for i, e in reversed(list(enumerate(c_string))):
        if not e.isspace():
            break
        trailing_spaces += 1

    return((leading_spaces, trailing_spaces))


def get_property(prop):
    currentdir = os.path.dirname(os.path.realpath(__file__))
    parentdir = os.path.dirname(currentdir)
    result = re.search(
        r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop),
        open(os.path.join(parentdir, '__init__.py')).read())
    return result.group(1)


def standards_latest(standards):
    return max([standard.version for standard in standards if standard.version] or ["0.1"],
               key=LooseVersion)


def lines_ranges(lines_spec):
    if not lines_spec:
        return None
    result = []
    for interval in lines_spec.split(","):
        (start, end) = interval.split("-")
        result.append(range(int(start), int(end) + 1))
    return result


def is_line_in_ranges(line, ranges):
    return not ranges or any([line in r for r in ranges])


def read_standards(settings):
    if not settings.rulesdir:
        abort("Standards directory is not set on command line or in configuration file - aborting")
    sys.path.append(os.path.abspath(os.path.expanduser(settings.rulesdir)))
    try:
        standards = importlib.import_module('standards')
    except ImportError as e:
        abort("Could not import standards from directory %s: %s" % (settings.rulesdir, str(e)))
    return standards


def read_config(config_file):
    config = configparser.RawConfigParser({'standards': None})
    config.read(config_file)

    return Settings(config, config_file)


def safe_load(string):
    """
    Parse the provided string returns a dict.
    :param string: A string to be parsed.
    :return: dict
    """
    try:
        return yaml.safe_load(string) or {}
    except yaml.scanner.ScannerError as e:
        print(str(e))


@contextlib.contextmanager
def open_file(filename, mode='r'):
    """
    Open the provide file safely and returns a file type.
    :param filename: A string containing an absolute path to the file to open.
    :param mode: A string describing the way in which the file will be used.
    :return: file type
    """
    with open(filename, mode) as stream:
        yield stream


def add_dict_branch(tree, vector, value):
    key = vector[0]
    tree[key] = value \
        if len(vector) == 1 \
        else add_dict_branch(tree[key] if key in tree else {},
                             vector[1:],
                             value)
    return tree
