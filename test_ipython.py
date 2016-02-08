"""Example use of jupyter_kernel_test, with tests for IPython."""

import unittest
import jupyter_kernel_test as jkt

class IRkernelTests(jkt.KernelTests):
    kernel_name = "python3"

    language_name = "python"

    file_extension = ".py"

    code_hello_world = "print('hello, world')"

    code_stderr = "import sys; print('test', file=sys.stderr)"

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

    code_execute_result = [
        {'code': "1+2+3", 'result': "6"},
        {'code': "[n*n for n in range(1, 4)]", 'result': "[1, 4, 9]"}
    ]

    code_display_data = [
        {'code': "from IPython.display import HTML, display; display(HTML('<b>test</b>'))",
         'mime': "text/html"},
        {'code': "from IPython.display import Math, display; display(Math('\\frac{1}{2}'))",
         'mime': "text/latex"}
    ]

    code_history_pattern = "1?2*"
    supported_history_operations = ("tail", "range", "search")

    code_inspect_sample = "zip"

    code_clear_output = "from IPython.display import clear_output; clear_output()"

if __name__ == '__main__':
    unittest.main()
