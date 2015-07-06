"""Machinery for testing Jupyter kernels via the messaging protocol.
"""

from unittest import TestCase, SkipTest
try:                  # Python 3
    from queue import Empty
except ImportError:   # Python 2
    from Queue import Empty

import abc

from jupyter_client.manager import start_new_kernel
from .kerneltest import TIMEOUT
from .messagespec import validate_message, MimeBundle

__version__ = '0.1'

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

    def execute_helper(self, code, timeout=TIMEOUT):
        msg_id = self.kc.execute(code=code)

        reply = self.kc.get_shell_msg(timeout=timeout)
        validate_message(reply, 'execute_reply', msg_id)

        busy_msg = self.kc.iopub_channel.get_msg(timeout=1)
        validate_message(busy_msg, 'status', msg_id)
        self.assertEqual(busy_msg['content']['execution_state'], 'busy')

        output_msgs = []
        while True:
            msg = self.kc.iopub_channel.get_msg(timeout=0.1)
            validate_message(msg, msg['msg_type'], msg_id)
            if msg['msg_type'] == 'status':
                self.assertEqual(msg['content']['execution_state'], 'idle')
                break
            elif msg['msg_type'] == 'execute_input':
                self.assertEqual(msg['content']['code'], code)
                continue
            output_msgs.append(msg)

        return reply, output_msgs

    code_hello_world = ""

    def test_execute_stdout(self):
        if not self.code_hello_world:
            raise SkipTest

        self.flush_channels()
        reply, output_msgs = self.execute_helper(code=self.code_hello_world)

        self.assertEqual(reply['content']['status'], 'ok')

        self.assertGreaterEqual(len(output_msgs), 1)
        self.assertEqual(output_msgs[0]['msg_type'], 'stream')
        self.assertEqual(output_msgs[0]['content']['name'], 'stdout')
        self.assertIn('hello, world', output_msgs[0]['content']['text'])

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
        if reply['content']['status'] != status:
            msg = "For code sample\n  {!r}\nExpected {!r}, got {!r}."
            raise AssertionError(msg.format(sample, status,
                                            reply['content']['status']))

    def test_is_complete(self):
        if not (self.complete_code_samples
                or self.incomplete_code_samples
                or self.invalid_code_samples):
            raise SkipTest

        self.flush_channels()

        for sample in self.complete_code_samples:
            self.check_is_complete(sample, 'complete')

        for sample in self.incomplete_code_samples:
            self.check_is_complete(sample, 'incomplete')

        for sample in self.invalid_code_samples:
            self.check_is_complete(sample, 'invalid')

    code_page_something = ""

    def test_pager(self):
        if not self.code_page_something:
            raise SkipTest

        self.flush_channels()

        reply, output_msgs = self.execute_helper(self.code_page_something)
        self.assertEqual(reply['content']['status'],  'ok')
        payloads = reply['content']['payload']
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]['source'], 'page')
        mimebundle = payloads[0]['data']
        # Validate the mimebundle
        MimeBundle().data = mimebundle
        self.assertIn('text/plain', mimebundle)
