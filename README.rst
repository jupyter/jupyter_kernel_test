===================
jupyter_kernel_test
===================

``jupyter_kernel_test`` is a tool for testing Jupyter_ kernels. It tests kernels
for successful code execution and conformance with the `Jupyter Messaging Protocol`_
(currently 5.0).

-------
Install
-------

Install it with pip (python3.4 or greater required)::

    pip3 install jupyter_kernel_test

-----
Usage
-----

To use it, you need to write a (python) ``unittest`` file containing code
samples in the relevant language which test various parts of the messaging protocol.
A short example is given below, and you can also refer to the
``test_ipykernel.py`` and ``test_irkernel.py`` files for complete examples.

Some parts of the messaging protocol are relevant only to the browser-based
notebook (rich display) or console interfaces (code completeness,
history searching). Only parts of the spec for which you provide code samples
are tested.

Run this file directly using python, or use ``nosetests`` or ``py.test`` to find
and run it.

-------
Example
-------

.. code-block:: python

    import unittest
    import jupyter_kernel_test


    class MyKernelTests(jupyter_kernel_test.KernelTests):
        # Required --------------------------------------

        # The name identifying an installed kernel to run the tests against
        kernel_name = "mykernel"

        # language_info.name in a kernel_info_reply should match this
        language_name = "mylanguage"

        # Optional --------------------------------------

        # Code in the kernel's language to write "hello, world" to stdout
        code_hello_world = "print 'hello, world'"

        # Pager: code that should display something (anything) in the pager
        code_page_something = "help(something)"

        # Samples of code which generate a result value (ie, some text
        # displayed as Out[n])
        code_execute_result = [{"code": "6*7", "result": "42"}]

        # Samples of code which should generate a rich display output, and
        # the expected MIME type
        code_display_data = [{"code": "show_image()", "mime": "image/png"}]

        # You can also write extra tests. We recommend putting your kernel name
        # in the method name, to avoid clashing with any tests that
        # jupyter_kernel_test adds in the future.
        def test_mykernel_stderr(self):
            self.flush_channels()
            reply, output_msgs = self.execute_helper(code='print_err "oops"')
            self.assertEqual(output_msgs[0]["header"]["msg_type"], "stream")
            self.assertEqual(output_msgs[0]["content"]["name"], "stderr")
            self.assertEqual(output_msgs[0]["content"]["text"], "oops\n")


    if __name__ == "__main__":
        unittest.main()

--------
Coverage
--------

The following aspects of the messaging protocol are not explicitly tested:

- Widget comms: ``comm_open``, ``comm_msg``, ``comm_close``
- stdin: ``input_request``, ``input_reply``
- display_data metadata
- Shutdown/restart: ``shutdown_request``, ``shutdown_reply``
- History: not all option combinations covered
- Inspection: multiple levels
- Execution payloads (deprecated but still used): payloads ``load``, ``edit``, ``ask_exit``
- User expressions
- Execution: combinations of ``silent``, ``store_history`` and ``stop_on_error``

.. _Jupyter: http://jupyter.org
.. _Jupyter Messaging Protocol: https://jupyter-client.readthedocs.io/en/latest/messaging.html
