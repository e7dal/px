import operator
import subprocess

import os
import re


# Match + group: "47536 root              0:00.03  0.0 /usr/sbin/cupsd -l"
PS_LINE = re.compile(" *([0-9]+) +([^ ]+) +([0-9:.]+) +([0-9.]+) +(.*)")

# Match + group: "1:02.03"
CPUTIME_OSX = re.compile("^([0-9]+):([0-9][0-9]\.[0-9]+)$")

# Match + group: "01:23:45"
CPUTIME_LINUX = re.compile("^([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")

# Match + group: "123-01:23:45"
CPUTIME_LINUX_DAYS = re.compile("^([0-9]+)-([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")


class PxProcess(object):
    def __init__(self, process_builder):
        self.pid = process_builder.pid

        self.username = process_builder.username

        self.cpu_time_s = seconds_to_str(process_builder.cpu_time)

        self.memory_percent_s = (
            "{:.0f}%".format(process_builder.memory_percent))

        self.cmdline = process_builder.cmdline

        self.score = (
            (process_builder.cpu_time + 1) *
            (process_builder.memory_percent + 1))

    def match(self, string):
        """
        Returns True if this process matches the string.

        See px_process_test.test_match() for the exact definition of how the
        matching is done.
        """
        if string is None:
            return True

        if self.username == string:
            return True

        if string in self.cmdline:
            return True

        if string in self.cmdline.lower():
            return True

        return False


class PxProcessBuilder(object):
    pass


def call_ps():
    """
    Call ps and return the result in an array of one output line per process
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]
    ps = subprocess.Popen(["ps", "-ax", "-o", "pid,user,time,%mem,command"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return ps.communicate()[0].splitlines()[1:]


def parse_time(timestring):
    """Convert a CPU time string returned by ps to a number of seconds"""

    match = CPUTIME_OSX.match(timestring)
    if match:
        minutes = int(match.group(1))
        seconds = float(match.group(2))
        return 60 * minutes + seconds

    match = CPUTIME_LINUX.match(timestring)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return 3600 * hours + 60 * minutes + seconds

    match = CPUTIME_LINUX_DAYS.match(timestring)
    if match:
        days = int(match.group(1))
        hours = int(match.group(2))
        minutes = int(match.group(3))
        seconds = int(match.group(4))
        return 86400 * days + 3600 * hours + 60 * minutes + seconds

    raise ValueError("Unparsable timestamp: <" + timestring + ">")


def ps_line_to_process(ps_line):
    match = PS_LINE.match(ps_line)
    assert match is not None

    process_builder = PxProcessBuilder()
    process_builder.pid = int(match.group(1))
    process_builder.username = match.group(2)
    process_builder.cpu_time = parse_time(match.group(3))
    process_builder.memory_percent = float(match.group(4))
    process_builder.cmdline = match.group(5)

    return PxProcess(process_builder)


def get_all():
    return map(lambda line: ps_line_to_process(line), call_ps())


def order_best_last(processes):
    """Returns process list ordered with the most interesting one last"""
    return sorted(processes, key=operator.attrgetter('score', 'cmdline'))


def seconds_to_str(seconds):
    if seconds < 60:
        seconds_s = str(seconds)
        decimal_index = seconds_s.rfind('.')
        if decimal_index > -1:
            # Chop to at most three decimals
            seconds_s = seconds_s[0:decimal_index + 4]
        return seconds_s + "s"

    if seconds < 3600:
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds - minutes * 60)
        return "{}m{:02d}s".format(minutes, remaining_seconds)

    if seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds - 3600 * hours) / 60)
        return "{}h{:02d}m".format(hours, minutes)

    days = int(seconds / 86400)
    hours = int((seconds - 86400 * days) / 3600)
    return "{}d{:02d}h".format(days, hours)