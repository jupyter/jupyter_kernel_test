jupyter_kernel_test is a tool for testing Jupyter kernels.

Install it with pip::

    pip install jupyter_kernel_test

Use it like this:

.. code-block:: python

    import unittest
    import jupyter_kernel_test

    class MyKernelTests(jupyter_kernel_test.KernelTests):
        # Required --------------------------------------

        # The name identifying an installed kernel to run the tests against
        kernel_name = "mykernel"

        # language_info.name in a kernel_info_reply should match this
        language_name = "dg"

        # language_info.file_extension, should match kernel_info_reply
        # (and start with a dot)
        file_extension = ".py"

        # Optional --------------------------------------

        # Code in the kernel's language to write "hello, world" to stdout
        code_hello_world = "print 'hello, world'"

        # code which should print something to stderr
        code_stderr = "import sys; print('test', file=sys.stderr)"

        # Tab completions: in each dictionary, text is the input, which it will
        # try to complete from the end of. matches is the collection of results
        # it should expect.
        completion_samples = [
            {
                'text': 'zi',
                'matches': {'zip'},
            },
        ]

        # Code completeness: samples grouped by expected result
        complete_code_samples = ['print "hi"']
        incomplete_code_samples = ['function a1 a2 ->', '"""in a string']
        invalid_code_samples = ['import = 7q']

        # Pager: code that should display something (anything) in the pager
        code_page_something = "help('foldl')"

        # Code which the frontend should display an error for
        code_generate_error = "raise"

        # Samples of code which generate a result value (ie, some text
        # displayed as Out[n])
        code_execute_result = [
            {'code': "1+2+3", 'result': "6"}
        ]

        # Samples of code which should generate a rich display output, and
        # the expected MIME type
        code_display_data = [
            {'code': "display(HTML('<b>test</b>'))", 'mime': "text/html"},
            {'code': "display(Math('\\frac{1}{2}'))", 'mime': "text/latex"}
        ]

        # Which types of history access should be tested (omit this attribute
        # or use an empty list to test nothing). For history searching,
        # code_history_pattern should be a glob-type match for one of the
        # code strings in code_execute_result
        supported_history_operations = ("tail", "range", "search")
        code_history_pattern = "1?2*"

        # A statement/object to which the kernel should respond with some
        # information when inspected
        code_inspect_sample = "zip"

        # Code which should cause the kernel to send a clear_output request
        # to the frontend
        code_clear_output = "clear_output()"

    if __name__ == '__main__':
        unittest.main()

Run this file directly using python, or use nosetests/py.test to find and
run it.
