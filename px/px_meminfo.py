import os
import re
import sys
import errno
import platform
import subprocess

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type    # NOQA
    from typing import List      # NOQA
    from typing import Tuple     # NOQA
    from typing import Optional  # NOQA


def get_meminfo():
    # type: () -> text_type

    CSI = u"\x1b["
    NORMAL = CSI + u"m"
    RED = CSI + u"1;37;41m"
    YELLOW = CSI + u"1;30;43m"
    GREEN = CSI + u"1;30;42m"

    total_ram_bytes, wanted_ram_bytes = _get_ram_numbers()
    percentage = (100.0 * wanted_ram_bytes) / total_ram_bytes

    ram_text = "".join([
        str(int(round(percentage))),
        "%  ",
        bytes_to_string(wanted_ram_bytes),
        "/",
        bytes_to_string(total_ram_bytes)
        ])

    # "80"? I made it up.
    if percentage < 80:
        color = GREEN
    elif percentage < 100:
        color = YELLOW
    else:
        color = RED

    return color + " " + ram_text + " " + NORMAL


def bytes_to_string(bytes_count):
    # type: (int) -> text_type
    """
    Turn byte counts into strings like "14MB"
    """
    KB = 1024 ** 1
    MB = 1024 ** 2
    GB = 1024 ** 3
    TB = 1024 ** 4

    if bytes_count < 7 * KB:
        return str(bytes_count) + "B"

    if bytes_count < 7 * MB:
        return str(int(round(float(bytes_count) / KB))) + "KB"

    if bytes_count < 7 * GB:
        return str(int(round(float(bytes_count) / MB))) + "MB"

    if bytes_count < 7 * TB:
        return str(int(round(float(bytes_count) / GB))) + "GB"

    return str(int(round(float(bytes_count) / TB))) + "TB"


def _get_ram_numbers():
    # type: () -> Tuple[int, int]
    """
    Returns a tuple containing two numbers:
    * Total amount of RAM installed in the machine (in bytes)
    * Wanted amount of RAM by the system (in bytes)

    If wanted > total it generally implies that we're swapping.
    """
    return_me = _get_ram_numbers_from_proc()
    if return_me is not None:
        return return_me

    vm_stat_lines = _get_vmstat_output_lines()
    if vm_stat_lines is not None:
        return_me = _get_ram_numbers_from_vm_stat_output(vm_stat_lines)
        if return_me is not None:
            return return_me

    uname = str(platform.uname())
    platform_s = uname + " Python " + sys.version

    raise IOError("Unable to get memory info " + platform_s)


def _get_ram_numbers_from_proc(proc_meminfo="/proc/meminfo"):
    # type: (str) -> Optional[Tuple[int, int]]
    try:
        with open(proc_meminfo) as f:
            for line in f:
                # FIXME: Write code here
                pass
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # /proc/meminfo not found, we're probably not on Linux
            return None

        raise

    raise Exception("FIXME: Not implemented")


def _get_vmstat_output_lines():
    # type: () -> Optional[List[text_type]]
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    try:
        vm_stat = subprocess.Popen(["vm_stat"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=env)
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # vm_stat not found, we're probably not on OSX
            return None

        raise

    vm_stat_stdout = vm_stat.communicate()[0].decode('utf-8')
    vm_stat_lines = vm_stat_stdout.split('\n')

    return vm_stat_lines


def _update_if_prefix(base, line, prefix):
    # type: (Optional[int], text_type, text_type) -> Optional[int]
    if not line.startswith(prefix):
        return base

    no_ending_dot = line.rstrip(".")

    return int(no_ending_dot[len(prefix):])


def _get_ram_numbers_from_vm_stat_output(vm_stat_lines):
    # type: (List[text_type]) -> Optional[Tuple[int, int]]

    PAGE_SIZE_RE = re.compile(r"page size of ([0-9]+) bytes")

    # List based on https://apple.stackexchange.com/a/196925/182882
    page_size_bytes = None
    pages_free = None
    pages_active = None
    pages_inactive = None
    pages_speculative = None
    pages_wired = None
    pages_anonymous = None
    pages_purgeable = None
    pages_compressed = None  # "Pages occupied by compressor"
    pages_uncompressed = None  # "Pages stored in compressor"

    for line in vm_stat_lines:
        page_size_match = PAGE_SIZE_RE.search(line)
        if page_size_match:
            page_size_bytes = int(page_size_match.group(1))
            continue

        pages_free = _update_if_prefix(pages_free, line, "Pages free:")
        pages_active = _update_if_prefix(pages_active, line, "Pages active:")
        pages_inactive = _update_if_prefix(pages_inactive, line, "Pages inactive:")
        pages_speculative = _update_if_prefix(pages_speculative, line, "Pages speculative:")
        pages_wired = _update_if_prefix(pages_wired, line, "Pages wired down:")
        pages_anonymous = _update_if_prefix(pages_anonymous, line, "Anonymous pages:")
        pages_purgeable = _update_if_prefix(pages_purgeable, line, "Pages purgeable:")
        pages_compressed = _update_if_prefix(pages_compressed, line, "Pages occupied by compressor:")
        pages_uncompressed = _update_if_prefix(pages_uncompressed, line, "Pages stored in compressor:")

    if page_size_bytes is None:
        return None
    if pages_free is None:
        return None
    if pages_active is None:
        return None
    if pages_inactive is None:
        return None
    if pages_speculative is None:
        return None
    if pages_wired is None:
        return None
    if pages_anonymous is None:
        return None
    if pages_purgeable is None:
        return None
    if pages_compressed is None:
        return None
    if pages_uncompressed is None:
        return None

    # In experiments, this has added up well to the amount of physical RAM in my machine
    total_ram_pages = \
        pages_free + pages_active + pages_inactive + pages_speculative + pages_wired + pages_compressed

    # This matches what the Activity Monitor shows in macOS 10.15.6
    #
    # For anonymous - purgeable: https://stackoverflow.com/a/36721309/473672
    #
    # NOTE: We want to add swapped out pages to this as well, since those also
    # represent a want for pages.
    wanted_ram_pages = \
        pages_anonymous - pages_purgeable + pages_wired + pages_compressed

    total_ram_bytes = total_ram_pages * page_size_bytes
    wanted_ram_bytes = wanted_ram_pages * page_size_bytes

    return (total_ram_bytes, wanted_ram_bytes)
