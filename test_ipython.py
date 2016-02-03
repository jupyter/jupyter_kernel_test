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

    code_generate_error = "raise"

    code_output_samples = [
        {'code': "1+1", 'result': "2"}
    ]

    code_mime_samples = [
        {'code': "from IPython.display import HTML; HTML('<b>test</b>')",
         'mime': "text/html"},
        {'code': "from IPython.display import Math; Math('\\frac{1}{2}')",
         'mime': "text/latex"}
    ]

if __name__ == '__main__':
    unittest.main()
