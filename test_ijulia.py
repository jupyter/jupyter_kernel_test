"""
A non-python example, with tests for IRKernel (irkernel.github.io).
(Beware of python quoting/string escaping rules being different to the
language being tested)
"""

import unittest

from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
import jupyter_kernel_test as jkt

class JuliaKernelTests(jkt.KernelTests):
    kernel_name = "julia"

    @classmethod
    def setUpClass(cls):
        manager = KernelSpecManager()
        specs = manager.find_kernel_specs()
        for name in specs:
            if name.startswith('julia'):
                cls.kernel_name = name
                break
        try:
            cls.km, cls.kc = jkt.start_new_kernel(kernel_name=cls.kernel_name)
        except NoSuchKernel:
            raise unittest.SkipTest("No julia kernel installed")

    language_name = "julia"

    file_extension = ".jl"

    code_hello_world = 'println("hello, world!")'

    completion_samples = [
        {
            'text': 'prin',
            'matches': {'print', 'println', 'printstyled'},
        },
    ]

    complete_code_samples = ['1', "println(\"hello, world!\")"]
    incomplete_code_samples = ["print('hello"]

    code_generate_error = "throw('hi')"

    code_execute_result = [
        {'code': 'using Plots; x = 1:10; y = rand(10); plot(x,y, label="my label")', 'mime': "image/svg+xml"},
    ]


if __name__ == '__main__':
    unittest.main()
