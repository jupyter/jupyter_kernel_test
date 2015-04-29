kerneltest is a tool for testing Jupyter kernels.

Use it like this:

.. code-block:: python

    import unittest
    import kerneltest

    class MyKernelTests(kerneltest.KernelTests):
        # Required --------------------------------------

        # The name identifying an installed kernel to run the tests against
        kernel_name = "mykernel"

        # language_info.name in a kernel_info_reply should match this
        language_name = "dg"

        # Code in the kernel's language to write "hello, world" to stdout
        code_hello_world = "print 'hello, world'"

        # Optional --------------------------------------

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

    if __name__ == '__main__':
        unittest.main()

Run this file directly using python, or use nosetests/py.test to find and run it.
