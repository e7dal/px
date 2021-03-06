import re
import random
import datetime

from px import px_file
from px import px_process
from px import px_ipc_map

import dateutil.tz
import dateutil.parser

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import MutableMapping  # NOQA
    from typing import Optional        # NOQA
    from typing import List            # NOQA

# An example time string that can be produced by ps
TIMESTRING = "Mon Mar  7 09:33:11 2016"
TIME = dateutil.parser.parse(TIMESTRING).replace(tzinfo=dateutil.tz.tzlocal())


def spaces(at_least=1, at_most=3):
    return " " * random.randint(at_least, at_most)


def now():
    return datetime.datetime.now().replace(tzinfo=dateutil.tz.tzlocal())


def create_process(pid=47536, ppid=1234,
                   timestring=TIMESTRING,
                   uid=0,
                   cpuusage="0.0",
                   cputime="0:00.03", mempercent="0.0",
                   commandline="/usr/sbin/cupsd -l",
                   now=now()):
    # type: (...) -> px_process.PxProcess
    psline = (spaces(at_least=0) +
              str(pid) + spaces() +
              str(ppid) + spaces() +
              timestring + spaces() +
              str(uid) + spaces() +
              cpuusage + spaces() +
              cputime + spaces() +
              mempercent + spaces() +
              commandline)

    return px_process.ps_line_to_process(psline, now)


def create_file(filetype,     # type: str
                name,         # type: str
                device,       # type: Optional[str]
                pid,          # type: int
                access=None,  # type: str
                inode=None,   # type: str
                fd=None,      # type: int
                fdtype=None,  # type: Optional[str]
                ):
    # type (...) -> px_file.PxFile

    # Remove leading [] group from name if any
    match = re.match(r'(\[[^]]*\] )?(.*)', name)
    assert match
    name = match.group(2)

    file = px_file.PxFile(pid, filetype)
    file.name = name

    file.device = device
    file.access = access
    file.inode = inode
    file.fd = fd
    file.fdtype = fdtype
    return file


def create_ipc_map(pid, all_files, is_root=False):
    # type: (int, List[px_file.PxFile], bool) -> px_ipc_map.IpcMap
    """Wrapper around IpcMap() so that we can test it"""
    pid2process = {}  # type: MutableMapping[int, px_process.PxProcess]
    for file in all_files:
        if file.pid in pid2process:
            continue
        pid2process[file.pid] = create_process(pid=file.pid)
    if pid not in pid2process:
        pid2process[pid] = create_process(pid=pid)

    processes = list(pid2process.values())
    random.shuffle(processes)

    process = pid2process[pid]

    return px_ipc_map.IpcMap(process, all_files, processes, is_root)


def fake_callchain(*args):
    # type: (*str) -> px_process.PxProcess
    procs = []
    for arg in args:
        procs.append(create_process(commandline=arg))

    parent = None
    for proc in procs:
        proc.parent = parent
        parent = proc

    return proc
