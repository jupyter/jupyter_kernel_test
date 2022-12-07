"""
A non-python example, with tests for xeus-cling kernel (https://github.com/jupyter-xeus/xeus-cling).
(Beware of python quoting/string escaping rules being different to the
language being tested)
"""

import unittest

from jupyter_client.kernelspec import NoSuchKernel

import jupyter_kernel_test as jkt


class XeusClingKernelTests(jkt.KernelTests):
    kernel_name = "xcpp17"

    @classmethod
    def setUpClass(cls):
        try:
            cls.km, cls.kc = jkt.start_new_kernel(kernel_name=cls.kernel_name)
        except NoSuchKernel:
            raise unittest.SkipTest("Xeus-Cling Kernel not installed") from None

    language_name = "c++"

    file_extension = ".cpp"

    code_hello_world = '#include <iostream>\nstd::cout << "hello, world!" << std::endl;'

    code_stderr = '#include <iostream>\nstd::cerr << "some error" << std::endl;'

    complete_code_samples = ["1", "int j=5"]
    incomplete_code_samples = ["double sqr(double a"]

    code_generate_error = 'throw std::runtime_error("Unknown exception");'

    code_execute_result = [
        {"code": "int j = 5;j", "result": "5"},
    ]


if __name__ == "__main__":
    unittest.main()
