"""
A non-python example, with tests for IRKernel (irkernel.github.io).
(Beware of python quoting/string escaping rules being different to the
language being tested)
"""

import subprocess
import unittest
import shutil

from jupyter_client.kernelspec import KernelSpecManager
import jupyter_kernel_test as jkt


class JuliaKernelTests(jkt.KernelTests):
    kernel_name = ""

    @classmethod
    def setUpClass(cls):
        if not shutil.which('julia'):
            raise unittest.SkipTest("Julia is not installed")
        # Make sure kernel and plotting library are installed.
        cmds = ['using Pkg; Pkg.add("IJulia")', 'using Pkg; Pkg.add("Plots")']
        for cmd in cmds:
            subprocess.check_call(["julia", "-e", cmd])
        # Find the installed kernel.
        manager = KernelSpecManager()
        specs = manager.find_kernel_specs()
        for name in specs:
            if name.startswith('julia'):
                cls.kernel_name = name
                break
        if not cls.kernel_name:
            raise unittest.SkipTest("Julia kernel is not installed")
        cls.km, cls.kc = jkt.start_new_kernel(kernel_name=cls.kernel_name)

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
