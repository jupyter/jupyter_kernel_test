"""
A non-python example, with tests for IRKernel (irkernel.github.io).
(Beware of python quoting/string escaping rules being different to the
language being tested)
"""

import os
import unittest

from jupyter_client.kernelspec import NoSuchKernel

import jupyter_kernel_test as jkt


class IRKernelTests(jkt.KernelTests):
    kernel_name = "ir"

    @classmethod
    def setUpClass(cls):
        try:
            cls.km, cls.kc = jkt.start_new_kernel(kernel_name=cls.kernel_name)
        except NoSuchKernel:
            raise unittest.SkipTest("No ir kernel installed") from None

    language_name = "R"

    file_extension = ".r"

    code_hello_world = 'print("hello, world")'

    completion_samples = (
        [
            {
                "text": "zi",
                "matches": {"zip"},
            },
        ]
        if os.name != "nt"
        else []
    )  # zip is not available on Windows

    complete_code_samples = ["1", "print('hello, world')", "f <- function(x) {x*2}"]
    incomplete_code_samples = ["print('hello", "f <- function(x) {x"]

    code_generate_error = "raise"

    code_display_data = [
        {"code": "plot(iris)", "mime": "image/png"},
        {"code": "1+2+3", "mime": "text/plain"},
    ]


if __name__ == "__main__":
    unittest.main()
