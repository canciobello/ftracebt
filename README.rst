====================
Ftrace Buffer Tester
====================

This is a set of tests for the ftrace ring buffer. We write to the buffer
through the *trace_marker* file and we read the buffer using the *trace*
file.


Installation
============

To keep things simple from now we are considering that all the commands are
being executed in a root shell (no need to use *sudo*).

Make sure you have *Python 3* and that it's available from your command line. You
can check this by simply running:

.. code-block:: bash

  $ python --version

  # in Ubuntu:
  $ python3 --version

Then check that you have *pip*:

.. code-block:: bash

  $ pip --version

  # in Ubuntu:
  $ pip3 --version

Consider updating your system before proceeding. You can install *pip* in
Ubuntu with:

.. code-block:: bash

  $ apt install python3-pip

Then install *pipenv*:

.. code-block:: bash

  $ pip3 install --user pipenv

Then add pipenv to your *PATH*:

.. code-block:: bash

  $ echo "export PATH=\$PATH:`python3 -m site --user-base`/bin" >> ~/.profile
  $ source ~/.profile
  # You could have to do this with the ~/.bashrc file too.

Clone or download the project:

.. code-block:: bash

  $ clone https://github.com/canciobello/ftracebt.git

Install project dependencies:

.. code-block:: bash

  $ cd ftracebt
  $ pipenv install

Usage
=====

Help
----

The script adds a few options besides the Pytest options. You can learn about
these options in the "custom options:" section in the output of:

.. code-block:: bash

  $ cd src/ftracebt
  $ pipenv run python -m pytest test_buffer.py --help

There is a configuration file *test_buffer.ini* where you can tweak a few
variables too. Consider to read Pytest doc `Usage and Invocations <https://docs.pytest.org/en/latest/usage.html>`
for Pytest specific options.


nr_pages_to_fillup_buffer and buffer_size_kb
--------------------------------------------

The configuration variable *nr_pages_to_fillup_buffer* depends on the size of
the buffer. In most cases, the default buffer size would slow down the tests
unnecessarily. We consider that *buffer_size_kb=32* is a good value. In this
case *nr_pages_to_fillup_buffer* should be 9 (its default value). Before
running any test, at least that you change *nr_pages_to_fillup_buffer*, you
should do:

.. code-block:: bash

  $ echo 32 > /sys/kernel/debug/tracing/buffer_size_kb


Persistent file
---------------

While developing a new feature for ftrace the team decided to explore the
reusing of the ring-buffer parsing infrastructure that backs the file 'trace'.
To test this course of action a 'persistent' file was created. The idea was
that the content of the 'persistent' file should be the same than the content
of the 'trace' file except for a few details. I will not go into the details of
the implementation of the 'persistent' file because is not necessary for this
context.

If you include the 'persistent' file as part of the parameter '--trace-files'
this script will read not just the 'trace' file but the 'persistent' file too,
and will test that both contents are the same except for those very well
defined differences. In other words, if you pass '--trace-files
/sys/kernel/debug/tracing/trace,/sys/kernel/debug/tracing/persistent' as
parameter the 'persistent' file will be tested. Of course, you would have to
patch your kernel to created the 'persistent' file.


Run just one test
-----------------

Pytest allows you to run just one test.

.. code-block:: bash

  $  pipenv run python -m pytest test_buffer.py::TestWithMarker::test_write_one_page

Each test is documented below. To list the available tests you can do:

.. code-block:: bash

  $ pipenv run python -m pytest test_buffer.py --collect-only

In the output of the above command the values between '[]' are parameters.
Each test could be executed several times with a different set of parameters
and each time will count in the stats as a different test execution.


Run all tests without testing the persistent file
-------------------------------------------------

.. code-block:: bash

  $ pipenv run python -m pytest test_buffer.py --verbose --exitfirst --capture=no --cpus-to-use 0,1 --max-writes-delay 40

The first three options are to control Pytest. They are described in the
Pytest doc.


Run all tests testing the persistent file
-----------------------------------------

.. code-block:: bash

  $ pipenv run python -m pytest test_buffer.py --verbose --exitfirst --capture=no --cpus-to-use 0,1 --max-writes-delay 40 --trace-files /sys/kernel/debug/tracing/trace,/sys/kernel/debug/tracing/persistent


Tests doc
---------

The tests were conceived to test that "everything is working well" while the
ring buffer is in 'differents internal statuses' giving its implementation.
With different internal status, we are referring to the different internal
variables values that lead to different path code execution while performing
the same high level operation e.g. add new page content.

For example, it could seem arbitrary the selection of writing 1...4 pages, but
the fact is that because how the ring buffer is implemented, the code path
executions could be different in each of those cases. A similar case happens
when you fill up the buffer compared with when you are just adding a page in
'in the middle'.

The content that we write to the ring buffer during the tests is generated in a
way that would make easy to debug issues like an entry out of order, buffer
pages in reverse order, missing pages and so on.


| *test_buffer.py::TestWithMarker::test_write_one_page*
| *test_buffer.py::TestWithMarker::test_write_two_page*
| *test_buffer.py::TestWithMarker::test_write_three_page*
| *test_buffer.py::TestWithMarker::test_write_four_page*
| **test_buffer.py::TestWithMarker::test_write_<X>_page:**
	
	These are simple tests that write X pages to the ring buffer with a
       	predefined content. The buffer content is read back to test that its
       	content is correct. These tests write just on one per-cpu-ring-buffer
	because they run in a single process.
|
|
| *test_buffer.py::TestWithMarker::test_fillup_buffer*
| *test_buffer.py::TestWithMarker::test_fillup_plus_one_page*
| *test_buffer.py::TestWithMarker::test_fillup_plus_two_page*
| *test_buffer.py::TestWithMarker::test_fillup_plus_three_page*
| *test_buffer.py::TestWithMarker::test_fillup_plus_four_page*
| **test_buffer.py::TestWithMarker::test_fillup_plus_X_page:**

	These tests fill up the ring buffer and write 0 - 4 extra pages.
	The buffer content is read back to test that its content is correct.
	These tests write just on one per-cpu-ring-buffer because they run in a
       	single process.
|
|
| **test_buffer.py::TestWithMarker::test_marker_multiple_cpus:**

	This test executes in parallel each of the above tests on each cpu
       	specified in the parameter '--cpus-to-use'. This allows us to test the
	behavior of the code that parses the per-cpu-ring-buffer and merges its
       	content.
	
	For example, with '--cpus-to-use 0,1,2' and while executing the test
       	'test_buffer.py::TestWithMarker::test_fillup_plus_one_page' this test
       	will create three parallel process one per cpu (0, 1 and 2) and execute
       	the writing part of the test. In this way we are writting in the
       	per-cpu-ring-buffer of each specified cpu. After all the writing
	processes are done, the ring buffer content is read to test that the
       	content is in order (timestamp) as well as to test that all the
       	content of each per cpu buffer was merged properly (completeness and
       	ordering).
|
|
| **test_buffer.py::TestWithMarker::test_with_the_tracers:**

	This test 'activate' each tracer passed through the parameter
       	"--tracers-to-test". The 'activation' last for the time passed
	through the parameter '--tracers_on_intervals'. Multiple tracer
	and times are combined creating several test executions.

	After activated for the specified time interval, the test deactivated
	the tracer and read the content of the 'trace' and 'persistent' file
	and compared them to see if they match (except for a very small and
       	pre-defined differences). This test is skipped if no 'persistent' file
       	is passed.

