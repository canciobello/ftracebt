import pytest
import pathlib
from helper import ArgumentError
from helper import Helpers
from ftrace import FtraceManager
from ftrace import ReadBuffer
from ftrace import WriteBuffer
from ftrace import Check


def pytest_addoption(parser):
    parser.addoption("--config-file",
                     default="test_buffer.ini",
                     help="Configuration file. Default value: test_buffer.ini")
    parser.addoption(
        "--default-cpu",
        type=int,
        default=0,
        help=
        "CPU ID to use when we are writing into the buffer while testing just on one CPU. It is not necessary that the CPU ID match the CPU ID where the script will be running because in this case is just content with no useful meaning. Default value: 0."
    )
    parser.addoption(
        "--max-writes-delay",
        type=int,
        default=0,
        help=
        "Max amount of microsecods to wait between the writting of entries in a CPU buffer. Default value: 0"
    )
    parser.addoption(
        "--cpus-to-use",
        default='0',
        help=
        "List of cpus numbers that the test will use to write in their ftrace's buffer. e.g. --cpu 0,1,3,5. Default value: 0."
    )
    parser.addoption(
        "--tracers-to-test",
        default='function,function_graph,events',
        help=
        "List of tracers names that will be used to write to the buffer. e.g. --tracers-to-test function,function_graph,events. Default value: function,function_graph,events."
    )
    parser.addoption(
        "--tracers_on_intervals",
        default='100,3000',
        help=
        "How long in milliseconds each 'tracers_to_test' will be on (writing content to the buffer) before we stop it to read the content. One test will be run for each possible combination of 'tracers_to_test' and 'tracers_on_intervals' values. e.g. --tracers_on_intervals 100,3000. Default value: 100,3000"
    )

    parser.addoption(
        "--trace-files",
        default='/sys/kernel/debug/tracing/trace',
        help=
        "The full path of the 'trace' file. If you want to test a 'persistent' file (you would need to patch the kernel) you can add its full path after a comma. e.g. --trace-files /sys/kernel/debug/tracing/trace,/sys/kernel/debug/tracing/persistent. Default value: /sys/kernel/debug/tracing/trace."
    )


@pytest.fixture(scope='session')
def cwd(request):
    return pathlib.Path(__file__).parent


@pytest.fixture(scope='session')
def config_filename(request):
    return request.config.getoption("--config-file")


@pytest.fixture(scope='session')
def default_cpu(request):
    return request.config.getoption("--default-cpu")


@pytest.fixture(scope='session')
def max_writes_delay(request):
    return request.config.getoption("--max-writes-delay")


@pytest.fixture(scope='session')
def cpus_to_use(request):
    try:
        return [
            int(cpu.strip())
            for cpu in request.config.getoption("--cpus-to-use").split(',')
        ]
    except Exception as err:
        raise ArgumentError(
            'Error in argument "--cpus-to-uses". Details: {}'.format(str(err)))


@pytest.fixture(scope='session')
def config(config_filename):
    return Helpers.get_config(config_filename)


@pytest.fixture(scope='session')
def writebuffer(config):
    return WriteBuffer(config)


@pytest.fixture(scope='session')
def buffercheck(config):
    return Check


@pytest.fixture(scope='session')
def trace_files(request):
    return [
        x.strip()
        for x in request.config.getoption('trace_files').split(',')
        if x
    ]


@pytest.fixture(scope='session')
def readbuffer(config, trace_files):
    return ReadBuffer(config, trace_files[0])


@pytest.fixture(scope='session')
def ftrace_manager(config, trace_files):
    return FtraceManager(config, trace_files[0])


@pytest.fixture(scope='session')
def marker_entries_per_page(config):
    return int(config['marker_entries_per_page'])


def pytest_generate_tests(metafunc):
    if "tracer_name" in metafunc.fixturenames:
        tracers_name = [
            x.strip()
            for x in metafunc.config.getoption('tracers_to_test').split(',')
            if x
        ]
        metafunc.parametrize("tracer_name", tracers_name)

    if "tracers_on_interval" in metafunc.fixturenames:
        tracers_on_intervals = [
            int(x.strip()) for x in metafunc.config.getoption(
                'tracers_on_intervals').split(',') if x
        ]
        metafunc.parametrize("tracers_on_interval", tracers_on_intervals)

    if "trace_files_tuple" in metafunc.fixturenames:
        trace_files = [
            x.strip()
            for x in metafunc.config.getoption('trace_files').split(',')
            if x
        ]
        if len(trace_files) == 2:
            metafunc.parametrize("trace_files_tuple", [tuple(trace_files)])
        else:
            metafunc.parametrize("trace_files_tuple", [])
