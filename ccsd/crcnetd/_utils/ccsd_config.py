# Copyright (C) 2006  The University of Waikato
#
# This file is part of crcnetd - CRCnet Configuration System Daemon
#
# Configuration File Handling - Provides a unified interface to the 
# configuration files used to control operation of the system
#
# Author:       Matt Brown <matt@crc.net.nz>
# Version:      $Id$
#
# crcnetd is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# crcnetd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# crcnetd; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import sys
import os.path
import ConfigParser
import getopt
import traceback
from ccsd_common import *
from ccsd_log import *

class ccs_config_error(ccsd_error):
    pass

_config = None

def config_init():
    global _config

    try:
        # Read configuration from config file
        _config = ConfigParser.ConfigParser()

        # Add config file specified on command line
        conffile = ""
        optlist, args = getopt.gnu_getopt(sys.argv[1:], OPTION_LIST)
        for (arg, val) in optlist:
            if arg == "-c":
                conffile =  val
            if arg == "-v":
                setVerbose()

        _config.read([DEFAULT_CONFFILE, conffile]) 
    except:
        (type, value, tb) = sys.exc_info()
        try:
            # ccsd_log may not have been initialised yet...
            log_fatal("Could not read configuration file!", sys.exc_info())
        except:
            print "Could not read configuration file!"
            for line in traceback.format_exception(type, value, tb): 
                print line.strip()
            sys.exit(1)

def config_get(section, option, default=None, raw=0, vars=None, obj=None):
    """Get a value from the configuration, with a default."""
    global _config
    if obj is None: obj=_config
    if obj is None: return default
    if section is None:
        section = os.path.basename(sys.argv[0])
    if obj.has_option(section, option):
        return obj.get(section, option, raw=raw, vars=None)
    else:
        return default
def config_getint(section, option, default=None, obj=None):
    """Get an integer value from the configuration, with a default."""
    global _config
    if obj is None: obj=_config
    if obj is None: return default
    if section is None:
        section = os.path.basename(sys.argv[0])
    if obj.has_option(section, option):
        return obj.getint(section, option)
    else:
        return default
def config_getboolean(section, option, default=None, obj=None):
    """Get a boolean value from the configuration, with a default."""
    global _config
    if obj is None: obj=_config
    if obj is None: return default
    if section is None:
        section = os.path.basename(sys.argv[0])
    if obj.has_option(section, option):
        return obj.getboolean(section, option)
    else:
        return default
def config_get_required(section, option, raw=0, vars=None, obj=None):
    global _config
    if obj is None: obj=_config
    if obj is None: return default
    if section is None:
        section = os.path.basename(sys.argv[0])
    if obj.has_option(section,option):
        return obj.get(section, option, raw=raw, vars=None)
    else:
        raise ccs_config_error("Configuration file is missing required " \
                "value '%s' from section '%s'" % (option , section))

def init_pref_store(preffile):
    """Open a configuration file to use for preference storage

    There is no real difference between this file and any other, except we
    return the configparser handle to the user instead of keeping it globally
    to allow the user to manage multiple preference stores if desired.
    """
    # Initialise a preference store object
    pref = ConfigParser.ConfigParser()
    pref.ccsd_filename = preffile
    
    # Read from the preference file
    pref.read(preffile) 

    return pref

def pref_get(section, option, store, default=None):
    """Returns a preference from the specified preference store"""
    return config_get(section, option, default=default, obj=store)
def pref_getint(section, option, store, default=None):
    """Returns a preference from the specified preference store"""
    return config_getint(section, option, default=default, obj=store)
def pref_getboolean(section, option, store, default=None):
    """Returns a preference from the specified preference store"""
    return config_getboolean(section, option, default=default, obj=store)
def pref_set(section, option, value, store):
    """Sets a preference to the specified value"""
    # Can't store a preference in an invalid store
    if store is None:
        log_error("Invalid preference stored passed to pref_set!")
        return None
    if section is None:
        section = os.path.basename(sys.argv[0])
    if not store.has_section(section):
        store.add_section(section)
    store.set(section, option, value)
    try:
        remountrw()
        fp = open(store.ccsd_filename, "w")
        store.write(fp)
        fp.close()
    finally:
        remountro()
