"""Example use of jupyter_kernel_test, with tests for IPython."""

import unittest
import jupyter_kernel_test as jkt

class IRkernelTests(jkt.KernelTests):
    kernel_name = "python3"

    language_name = "python"

    code_hello_world = "print('hello, world')"

    completion_samples = [
        {
            'text': 'zi',
            'matches': {'zip'},
        },
    ]

    complete_code_samples = ['1', "print('hello, world')", "def f(x):\n  return x*2\n\n"]
    incomplete_code_samples = ["print('''hello", "def f(x):\n  x*2"]

    code_page_something = "zip?"

if __name__ == '__main__':
    unittest.main()
