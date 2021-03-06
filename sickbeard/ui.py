# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime

import sickbeard

MESSAGE = 'notice'
ERROR = 'error'


class Notifications(object):
    """
    A queue of Notification objects.
    """
    def __init__(self):
        self._messages = []
        self._errors = []

    def message(self, title, message=''):
        """
        Add a regular notification to the queue

        title: The title of the notification
        message: The message portion of the notification
        """
        self._messages.append(Notification(title, message, MESSAGE))

    def error(self, title, message=''):
        """
        Add an error notification to the queue

        title: The title of the notification
        message: The message portion of the notification
        """
        self._errors.append(Notification(title, message, ERROR))

    def get_notifications(self, remote_ip='127.0.0.1'):
        """
        Return all the available notifications in a list. Marks them all as seen
        as it returns them. Also removes timed out Notifications from the queue.

        Returns: A list of Notification objects
        """

        # filter out expired notifications
        self._errors = [x for x in self._errors if not x.is_expired()]
        self._messages = [x for x in self._messages if not x.is_expired()]

        # return any notifications that haven't been shown to the client already
        return [x.see(remote_ip) for x in self._errors + self._messages if x.is_new(remote_ip)]

# static notification queue object
notifications = Notifications()


class Notification(object):
    """
    Represents a single notification. Tracks its own timeout and a list of which clients have
    seen it before.
    """
    def __init__(self, title, message='', type=None, timeout=None):
        self.title = title
        self.message = message

        self._when = datetime.datetime.now()
        self._seen = []

        if type:
            self.type = type
        else:
            self.type = MESSAGE

        if timeout:
            self._timeout = timeout
        else:
            self._timeout = datetime.timedelta(minutes=1)

    def is_new(self, remote_ip='127.0.0.1'):
        """
        Returns True if the notification hasn't been displayed to the current client (aka IP address).
        """
        return remote_ip not in self._seen

    def is_expired(self):
        """
        Returns True if the notification is older than the specified timeout value.
        """
        return datetime.datetime.now() - self._when > self._timeout

    def see(self, remote_ip='127.0.0.1'):
        """
        Returns this notification object and marks it as seen by the client ip
        """
        self._seen.append(remote_ip)
        return self


class ProgressIndicator(object):

    def __init__(self, percentComplete=0, currentStatus=None):
        self.percentComplete = percentComplete
        self.currentStatus = currentStatus or {'title': ''}


class ProgressIndicators(object):
    _pi = {'massUpdate': [],
           'massAdd': [],
           'dailyUpdate': []
           }

    @staticmethod
    def getIndicator(name):
        if name not in ProgressIndicators._pi:
            return []

        # if any of the progress indicators are done take them off the list
        for curPI in ProgressIndicators._pi[name]:
            if curPI is not None and curPI.percentComplete() == 100:
                ProgressIndicators._pi[name].remove(curPI)

        # return the list of progress indicators associated with this name
        return ProgressIndicators._pi[name]

    @staticmethod
    def setIndicator(name, indicator):
        ProgressIndicators._pi[name].append(indicator)


class QueueProgressIndicator(object):
    """
    A class used by the UI to show the progress of the queue or a part of it.
    """
    def __init__(self, name, queueItemList):
        self.queueItemList = queueItemList
        self.name = name

    def numTotal(self):
        return len(self.queueItemList)

    def numFinished(self):
        return len([x for x in self.queueItemList if not x.is_in_queue()])

    def numRemaining(self):
        return len([x for x in self.queueItemList if x.is_in_queue()])

    def nextName(self):
        for curItem in [sickbeard.showQueueScheduler.action.currentItem] + sickbeard.showQueueScheduler.action.queue:  # @UndefinedVariable
            if curItem in self.queueItemList:
                return curItem.name

        return "Unknown"

    def percentComplete(self):
        numFinished = self.numFinished()
        numTotal = self.numTotal()

        if numTotal == 0:
            return 0
        else:
            return int(float(numFinished) / float(numTotal) * 100)


class LoadingTVShow(object):
    def __init__(self, dir):
        self.dir = dir
        self.show = None
