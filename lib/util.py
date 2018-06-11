import time, psutil, math
import sys
from threading import Timer

class Stopwatch(object):
    def __init__(self):
        if sys.platform == "win32":
            self.starttime = time.clock()
        else:
            self.starttime = time.time()
        self.stoptime = None
        self.running = True

    def elapsed(self):
        if self.running:
            if sys.platform == "win32":
                elapsed = time.clock() - self.starttime
            else:
                elapsed = time.time() - self.starttime
        else:
            elapsed = self.stoptime - self.starttime
        return elapsed

    def elapsed_minutes(self):
        return self.elapsed()/60

    def stop(self):
        self.stoptime = time.clock()
        self.running = False

class SystemInfo(object):
    def __init__(self):
        self.last_cpu_percent = None
        self.last_disk_usage = None
        self.last_cpu_time_percent = None
        self.last_available_memory = None

    def print_all_known_info(self):
        self.get_cpu_percent()
        self.get_disk_usage()
        self.get_cpu_time_percent()
        self.get_available_memory()

    def get_cpu_percent(self):
        previous = self.last_cpu_percent
        self.last_cpu_percent = psutil.cpu_percent()

        if previous is not None:
            diff = abs(self.last_cpu_percent - previous)
        else:
            diff = "No known previous cpu %"
        print "*INFO* CPU Percent Info\nLast known %: {}\n Current %: {}\n Difference: {}".format(previous, self.last_cpu_percent, diff)
        return self.last_cpu_percent

    def get_disk_usage(self, path='/'):
        previous = self.last_disk_usage
        self.last_disk_usage = psutil.disk_usage(path)
        print "*INFO* CPU Disk Usage\nLast known: {}\n Current: {}".format(previous, self.last_disk_usage)
        return self.last_disk_usage

    def get_cpu_time_percent(self):
        previous = self.last_cpu_time_percent
        self.last_cpu_time_percent = psutil.cpu_times_percent()
        print "*INFO* CPU Time Percent\nLast known: {}\n Current: {}".format(previous, self.last_cpu_time_percent)
        return self.last_cpu_time_percent

    def get_available_memory(self):
        previous = self.last_available_memory
        current = self.last_available_memory = psutil.virtual_memory().available
        print "*INFO* Available Memory\nLast known: {}\n Current: {}".format(previous, current)
        return current

class PeriodicScheduler(object):
    def __init__(self, interval, handler, handler_args=(), immediate_start=False):
        assert interval, "Invalid interval '{}' for PeriodicScheduler".format(interval)
        assert handler, "No Handler Provided for PeriodicScheduler"

        self._event_args = (handler, handler_args)
        self.scheduler = None
        self.interval = interval
        if immediate_start:
            self._event()
        else:
            self.kick()

    def _event(self):
        handler = self._event_args[0]
        handler_args = self._event_args[1]
        handler(*handler_args)
        self.kick()

    def kick(self):
        self.scheduler = Timer(self.interval, self._event, ())
        self.scheduler.daemon = True
        self.scheduler.start()

    def stop(self):
        if self.scheduler:
            self.scheduler.cancel()
