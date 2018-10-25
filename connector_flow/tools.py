# -*- coding: utf-8 -*-
from datetime import datetime

import pytz


def now(tz=None):
    """
    Returns the current datetime in the specified timezone (default: UTC)
    """
    # use utcnow() instead of now() to have a well-defined timezone
    result = datetime.utcnow()
    result = pytz.UTC.localize(result)
    if tz:
        if isinstance(tz, basestring):
            tz = pytz.timezone(tz)
        result = result.astimezone(tz)
    return result
