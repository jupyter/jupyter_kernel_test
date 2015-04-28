from unittest import TestCase, SkipTest
try:                  # Python 3
    from queue import Empty
except ImportError:   # Python 2
    from Queue import Empty

import abc

from jupyter_client.manager import start_new_kernel
from .kerneltest import TIMEOUT
from .messagespec import validate_message

class KernelTests(TestCase):
    kernel_name = ""

    @classmethod
    def setUpClass(cls):
        cls.km, cls.kc = start_new_kernel(kernel_name=cls.kernel_name)

    @classmethod
    def tearDownClass(cls):
        cls.kc.stop_channels()
        cls.km.shutdown_kernel(now=True)

    def flush_channels(self):
        for channel in (self.kc.shell_channel, self.kc.iopub_channel):
            while True:
                try:
                    msg = channel.get_msg(block=True, timeout=0.1)
                except Empty:
                    break
                else:
                    validate_message(msg)

    language_name = ""

    def test_kernel_info(self):
        self.flush_channels()

        msg_id = self.kc.kernel_info()
        reply = self.kc.get_shell_msg(timeout=TIMEOUT)
        validate_message(reply, 'kernel_info_reply', msg_id)

        if self.language_name:
            self.assertEqual(reply['content']['language_info']['name'],
                             self.language_name)
