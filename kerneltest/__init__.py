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

    code_hello_world = ""

    def test_execute_stdout(self):
        if not self.code_hello_world:
            raise SkipTest

        self.flush_channels()
        msg_id = self.kc.execute(code=self.code_hello_world)

        iopub_msg = self.kc.iopub_channel.get_msg(timeout=TIMEOUT)
        if iopub_msg['msg_type'] == 'status':
            validate_message(iopub_msg, 'status', msg_id)
            self.assertEqual(iopub_msg['content']['execution_state'], 'busy')
            iopub_msg = self.kc.iopub_channel.get_msg(timeout=TIMEOUT)
        validate_message(iopub_msg, 'execute_input', msg_id)
        self.assertEqual(iopub_msg['content']['code'], self.code_hello_world)

        iopub_msg = self.kc.iopub_channel.get_msg(timeout=TIMEOUT)
        validate_message(iopub_msg, 'stream', msg_id)
        self.assertEqual(iopub_msg['content']['name'], 'stdout')
        self.assertIn('hello, world', iopub_msg['content']['text'])

        reply = self.kc.get_shell_msg(timeout=TIMEOUT)
        validate_message(reply, 'execute_reply', msg_id)
        self.assertEqual(reply['content']['status'], 'ok')

    completion_samples = []

    def test_completion(self):
        if not self.completion_samples:
            raise SkipTest

        for sample in self.completion_samples:
            msg_id = self.kc.complete(sample['text'])
            reply = self.kc.get_shell_msg()
            validate_message(reply, 'complete_reply', msg_id)
            if 'matches' in sample:
                self.assertEqual(set(reply['content']['matches']),
                                 set(sample['matches']))

    complete_code_samples = []
    incomplete_code_samples = []
    invalid_code_samples = []

    def check_is_complete(self, sample, status):
        msg_id = self.kc.is_complete(sample)
        reply = self.kc.get_shell_msg()
        validate_message(reply, 'is_complete_reply', msg_id)
        self.assertEqual(reply['content']['status'], status)

    def test_is_complete(self):
        if not (self.complete_code_samples
                or self.incomplete_code_samples
                or self.invalid_code_samples):
            raise SkipTest

        for sample in self.complete_code_samples:
            self.check_is_complete(sample, 'complete')

        for sample in self.incomplete_code_samples:
            self.check_is_complete(sample, 'incomplete')

        for sample in self.invalid_code_samples:
            self.check_is_complete(sample, 'invalid')

