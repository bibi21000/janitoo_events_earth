# -*- coding: utf-8 -*-
"""The 1-wire Bus
It handle all communications to the onewire bus

"""

__license__ = """
    This file is part of Janitoo.

    Janitoo is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Janitoo is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Janitoo. If not, see <http://www.gnu.org/licenses/>.

"""
__author__ = 'Sébastien GALLET aka bibi21000'
__email__ = 'bibi21000@gmail.com'
__copyright__ = "Copyright © 2013-2014-2015-2016 Sébastien GALLET aka bibi21000"

import os
import time

import logging
logger = logging.getLogger(__name__)

from janitoo.bus import JNTBus
from janitoo.value import JNTValue, value_config_poll
from janitoo.node import JNTNode
from janitoo.component import JNTComponent

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_METER = 0x0032
COMMAND_CONFIGURATION = 0x0070

assert(COMMAND_DESC[COMMAND_METER] == 'COMMAND_METER')
assert(COMMAND_DESC[COMMAND_CONFIGURATION] == 'COMMAND_CONFIGURATION')
##############################################################

from janitoo_events import OID

def make_dawndusk(**kwargs):
    return DawnDusk(**kwargs)

class DawnDusk(JNTComponent):
    """ Provides the interface for a DS18B20 device. """

    def __init__(self, bus=None, addr=None, lock=None, unit="°C", **kwargs):
        """ Constructor.
        """
        JNTComponent.__init__(self,
            oid = kwargs.pop('oid', '%s.dawndusk'%OID),
            bus = bus,
            addr = addr,
            name = kwargs.pop('name', "Dawn/Dusk event"),
            product_name = kwargs.pop('product_name', "Dawn/Dusk event"),
            **kwargs)

