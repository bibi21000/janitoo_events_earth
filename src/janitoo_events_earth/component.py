# -*- coding: utf-8 -*-
"""The Raspberry hardware worker

The cron manager

A cron hold multiple values on multiples nodes.
Look at zwave crons

Ideally when defining a cron on janitoo for a node, we should "cascade" it : if the controller of the node support it, we sould add this cron on it too.

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
__copyright__ = "Copyright © 2013-2014-2015 Sébastien GALLET aka bibi21000"

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+                                   # pragma: no cover
    from logging import NullHandler                   # pragma: no cover
except ImportError:                                   # pragma: no cover
    class NullHandler(logging.Handler):               # pragma: no cover
        """NullHandler logger for python 2.6"""       # pragma: no cover
        def emit(self, record):                       # pragma: no cover
            pass                                      # pragma: no cover
logger = logging.getLogger(__name__)

import os, sys
import threading
from random import randint
from pkg_resources import get_distribution, DistributionNotFound
from janitoo.thread import JNTBusThread
from janitoo.options import get_option_autostart
from janitoo.utils import HADD
from janitoo.node import JNTNode
from janitoo.bus import JNTBus
from janitoo.component import JNTComponent
from janitoo.value import JNTValue, value_config_poll

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_METER = 0x0032
COMMAND_CONFIGURATION = 0x0070
COMMAND_METER = 0x0032
COMMAND_EVENT_ACTIVATION = 0x1010
COMMAND_EVENT_ACTUATOR_CONF = 0x1011
COMMAND_EVENT_CONTROLLER_CONF = 0x1012

assert(COMMAND_DESC[COMMAND_METER] == 'COMMAND_METER')
assert(COMMAND_DESC[COMMAND_METER] == 'COMMAND_METER')
assert(COMMAND_DESC[COMMAND_EVENT_ACTIVATION] == 'COMMAND_EVENT_ACTIVATION')
assert(COMMAND_DESC[COMMAND_EVENT_ACTUATOR_CONF] == 'COMMAND_EVENT_ACTUATOR_CONF')
assert(COMMAND_DESC[COMMAND_EVENT_CONTROLLER_CONF] == 'COMMAND_EVENT_CONTROLLER_CONF')
assert(COMMAND_DESC[COMMAND_CONFIGURATION] == 'COMMAND_CONFIGURATION')
##############################################################

def make_thread(options):
    if get_option_autostart(options, 'crons') == True:
        return CronsThread(options)
    else:
        return None

def make_event(**kwargs):
    return EventComponent(**kwargs)

class EventsThread(JNTBusThread):
    """The Hardware thread

    """
    def init_bus(self):
        """Build the bus
        """
        self.section = 'events'
        self.bus = CronsBus(options=self.options, oid=self.section, name='Cron Manager bus', product_name="Cron controller")


class EventsBus(JNTBus):
    """A pseudo-bus to manage all events
    """
    def __init__(self, manager_id=None, **kwargs):
        """
        :param int manager_id: the id of the manager
        :param kwargs: parameters
        """
        JNTBus.__init__(self, **kwargs)
        if manager_id == None:
            self.manager_id = randint(0,9999)
        else:
            self.manager_id = manager_id
        for cls in [COMMAND_EVENT_CONTROLLER_CONF, COMMAND_EVENT_ACTUATOR_CONF, COMMAND_CONFIGURATION]:
            self.cmd_classes.append(cls)
        uuid = 'manager_id'
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='The id of the event manager',
                    label='%s' % uuid,
                    index=0,
                    cmd_class=0x0070,
                    genre=0x03,
                    type=0x02,
                    set_data_cb=self.set_config_manager_id,
                    get_data_cb=self.get_config_manager_id,
                    is_writeonly=False,
                    is_readonly=False,
                    default=1,
                    )
        uuid = "add_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Add the event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.add_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "remove_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Remove the event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.remove_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "get_num_events"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Get the number of events',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.get_num_events,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "get_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Get all the values in a event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.get_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "add_value_to_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Add a value to a event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.add_value_to_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "set_value_in_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Set a value in a event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.set_value_in_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )
        uuid = "remove_value_from_event"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Remove a value from a event',
                    label='%s' % uuid,
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_CONTROLLER_CONF,
                    genre=0x05,
                    type=0x15,
                    set_data_cb=self.remove_value_from_event,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )

    def set_config_manager_id(self, node_uuid, index, data):
        """
        """
        try:
            self.manager_id = data
            self.options.set_option(self.node.uuid, 'manager_id', self.manager_id)
            if self._trigger_thread_reload_cb is not None:
                self._trigger_thread_reload_cb(self.node.config_timeout)
        except:
            logger.exception('Exception when writing config manager_id')

    def get_config_manager_id(self, node_uuid, index):
        """
        """
        try:
            self.manager_id =self.options.get_option(self.node.uuid, 'manager_id')
            return self.manager_id
        except:
            logger.exception('Exception when retrieving config manager_id')
        return None

    def add_event(self, name):
        """Create a event with name. Also have an uuid (index) on the controller
        """
        pass

    def remove_event(self, index):
        """Delete the event at index
        """
        pass

    def get_num_events(self, index):
        """Return the number of event in the controller
        """
        pass

    def get_event(self, index):
        """Return all the values attached to the event
        """
        pass

    def add_value_to_event(self, index, hadd, value_uuid, data):
        """Add a value to an existing event.
        """
        pass

    def set_value_in_event(self, index, hadd, value_uuid, data):
        """Update a value in an existing event.
        """
        pass

    def remove_value_from_event(self, index, hadd, value_uuid ):
        """Remove a value from a event
        """
        pass

class EventComponent(JNTComponent):
    """
    This component hold a event and all values attached to it
    """
    def __init__(self, bus=None, addr=None, **kwargs):
        JNTComponent.__init__(self, 'events.generic', bus=bus, addr=addr, name="A janitoo cron", **kwargs)
        self.values_in_cron = {}
        """The values attached to the cron
        {(hadd,value_uuid) : {'hadd':'0000/0000', 'value_uuid':'dim_swt_ff','data:'26'}}
        """
        uuid = "activate"
        self.values[uuid] = JNTValue( uuid=uuid,
                    help='Activate the cron',
                    label='activate',
                    units='',
                    index=0,
                    cmd_class=COMMAND_EVENT_ACTIVATION,
                    genre=0x02,
                    type=0x04,
                    set_data_cb=self.activate,
                    is_writeonly=True,
                    node_uuid=self.uuid,
                    )

    def activate(self, node_uuid, index):
        """ Activate the cron : send all the values
        """
        pass


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
__copyright__ = "Copyright © 2013-2014-2015 Sébastien GALLET aka bibi21000"

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+                                   # pragma: no cover
    from logging import NullHandler                   # pragma: no cover
except ImportError:                                   # pragma: no cover
    class NullHandler(logging.Handler):               # pragma: no cover
        """NullHandler logger for python 2.6"""       # pragma: no cover
        def emit(self, record):                       # pragma: no cover
            pass                                      # pragma: no cover
logger = logging.getLogger(__name__)
from janitoo.bus import JNTBus
from janitoo.value import JNTValue, value_config_poll
from janitoo.node import JNTNode
from janitoo.component import JNTComponent
import os
import time

##############################################################
#Check that we are in sync with the official command classes
#Must be implemented for non-regression
from janitoo.classes import COMMAND_DESC

COMMAND_METER = 0x0032
COMMAND_CONFIGURATION = 0x0070

assert(COMMAND_DESC[COMMAND_METER] == 'COMMAND_METER')
assert(COMMAND_DESC[COMMAND_CONFIGURATION] == 'COMMAND_CONFIGURATION')
##############################################################

def make_dawndusk(**kwargs):
    return DawnDusk(**kwargs)

class DawnDusk(JNTComponent):
    """ Provides the interface for a DS18B20 device. """

    def __init__(self, bus=None, addr=None, lock=None, unit="°C", **kwargs):
        """ Constructor.

        Arguments:
            bus:
                a 1-Wire instance representing the bus this device is
                connected to
            addr:
                the 1-Wire device address (in 7 bits format)
        """
        JNTComponent.__init__(self, 'events.dawndusk', bus=bus, addr=addr, name="Dawn/Dusk", **kwargs)

