#!/usr/bin/env python
"""
Applicability logic determines if a setting, alarm, or monitor are applicable at any given time.

    Version Notes:
        1.0.0.0 - 12/14/2019 - Created file for processing applicability logic.
        1.0.1.0 - 12/19/2019 - Updated to reflect change from volume targeted setting to separate volume targeted modes.
        1.0.2.0 - 01/19/2020 - Moved logic to separate applicability modules and created a loader function.
        1.0.2.1 - 01/24/2020 - Moved to generalized version number.
        1.0.2.2 - 02/05/2020 - Created setup function to access data container directly after exec command.

"""

__author__ = "John Dorian for Sai Systems Technologies"
__copyright__ = "Copyright 2019"
__version__ = "1.0.2.2"


def lookup_applicability(data, new_ver: str = None):
    """
    Lookup applicability definitions from VOCSN software version
    :param data: VOCSN data container.
    :param new_ver: Optionally specify a version.
    :return: ApplicabilityTracker
    """

    # Dynamically import applicability definitions
    ver = new_ver if new_ver else data.gen_version
    command = "from definitions.applicability.applicability_{} import ApplicabilityTracker as DEFS; defs = DEFS()" \
        .format(ver)
    _locals = locals()
    exec(command, globals(), _locals)
    applicability = _locals["defs"]
    applicability.setup(data)
    return applicability


class ApplicabilityItem:
    """ This placeholder is used to track objects that need applicability updates after batch processing. """

    def __init__(self, param, obj):
        """
        Initialize.
        :param param: Data model (Setting or MonitorChannel) Must have "applicable" attribute.
        :param obj: Any object needing update. Must have an attribute named "applicable".
        """
        self.obj = obj
        self.param = param


class ApplicabilityStack:
    """ Track objects that need applicability updates after completely processing an event. """

    def __init__(self):
        """ Initialize. """

        # Variables
        self.items = []

    def add_item(self, param, obj):
        """ Add object to stack for updating at end of read loop. """
        item = ApplicabilityItem(param, obj)
        self.items.append(item)

    def update(self):
        """ Update objects in stack with current applicability. """
        for item in self.items:
            app = item.param.applicable
            item.obj.applicable = app
        self.items = []
