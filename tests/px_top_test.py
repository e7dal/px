import os

from px import px_top
from px import px_process
from px import px_load_bar

from . import testutils


def test_adjust_cpu_times():
    now = testutils.now()

    current = [
        px_process.create_kernel_process(now),
        testutils.create_process(pid=100, cputime="0:10.00", commandline="only in current"),
        testutils.create_process(pid=200, cputime="0:20.00", commandline="re-used PID baseline",
                                 timestring="Mon May 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:30.00", commandline="relevant baseline"),
    ]
    baseline = [
        px_process.create_kernel_process(now),
        testutils.create_process(pid=200, cputime="0:02.00", commandline="re-used PID baseline",
                                 timestring="Mon Apr 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:03.00", commandline="relevant baseline"),
        testutils.create_process(pid=400, cputime="0:03.00", commandline="only in baseline"),
    ]

    actual = px_process.order_best_last(px_top.adjust_cpu_times(baseline, current))
    expected = px_process.order_best_last([
        px_process.create_kernel_process(now),
        testutils.create_process(pid=100, cputime="0:10.00", commandline="only in current"),
        testutils.create_process(pid=200, cputime="0:20.00", commandline="re-used PID baseline",
                                 timestring="Mon May 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:27.00", commandline="relevant baseline"),
    ])

    assert actual == expected


def test_get_toplist():
    # Just make sure this call doesn't crash
    px_top.get_toplist(px_process.get_all(), px_process.get_all())


def test_getch():
    pipe = os.pipe()
    read, write = pipe
    os.write(write, b'q')

    # We should get unicode responses from getch()
    assert px_top.getch(timeout_seconds=0, fd=read) == u'q'


def test_get_command():
    pipe = os.pipe()
    read, write = pipe
    os.write(write, b'q')

    assert px_top.get_command(timeout_seconds=0, fd=read) == px_top.CMD_QUIT


def test_sigwinch_handler():
    # Args ignored at the time of writing this, fill in better values if needed
    px_top.sigwinch_handler(None, None)

    # sys.stdin doesn't work when STDIN has been redirected (as during testing),
    # so we need to explicitly use the STDIN fd here. Try removing it and you'll
    # see :).
    STDIN = 0
    assert px_top.get_command(timeout_seconds=0, fd=STDIN) == px_top.CMD_RESIZE


def test_redraw():
    # Just make sure it doesn't crash
    loadbar = px_load_bar.PxLoadBar(1, 1)
    baseline = px_process.get_all()
    px_top.redraw(loadbar, baseline, 100, 10, clear=False)


def test_get_screen_lines_low_screen():
    loadbar = px_load_bar.PxLoadBar(1, 1)
    baseline = px_process.get_all()

    SCREEN_ROWS = 10
    SCREEN_COLUMNS = 70
    lines = px_top.get_screen_lines(
        loadbar, baseline, SCREEN_ROWS, SCREEN_COLUMNS)

    # Top row should contain ANSI escape codes
    CSI = u"\x1b["
    assert u'CSI' in lines[0].replace(CSI, u'CSI')

    assert len(lines) == SCREEN_ROWS

    # Lines should either be at most screen width long, or contain ANSI escapes
    for line in lines:
        assert (len(line) <= SCREEN_COLUMNS) or (u'CSI' in line.replace(CSI, u'CSI'))


def test_get_screen_lines_high_screen():
    loadbar = px_load_bar.PxLoadBar(1, 1)
    baseline = px_process.get_all()

    SCREEN_ROWS = 100
    SCREEN_COLUMNS = 70
    lines = px_top.get_screen_lines(
        loadbar, baseline, SCREEN_ROWS, SCREEN_COLUMNS)

    # Top row should contain ANSI escape codes
    CSI = u"\x1b["
    assert u'CSI' in lines[0].replace(CSI, u'CSI')

    assert len(lines) == SCREEN_ROWS

    # Lines should either be at most screen width long, or contain ANSI escapes
    for line in lines:
        assert (len(line) <= SCREEN_COLUMNS) or (u'CSI' in line.replace(CSI, u'CSI'))


def test_get_screen_lines_returns_enough_lines():
    loadbar = px_load_bar.PxLoadBar(1, 1)
    baseline = px_process.get_all()

    SCREEN_ROWS = 100000
    SCREEN_COLUMNS = 70
    lines = px_top.get_screen_lines(
        loadbar, baseline, SCREEN_ROWS, SCREEN_COLUMNS)

    assert len(lines) == SCREEN_ROWS
