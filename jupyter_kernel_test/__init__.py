"""Machinery for testing Jupyter kernels via the messaging protocol.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from unittest import TestCase, SkipTest

from jupyter_kernel_mgmt.discovery import KernelFinder
from jupyter_kernel_mgmt.client import BlockingKernelClient, ErrorInKernel
from .msgspec_v5 import validate_message

TIMEOUT = 15

__version__ = '0.3'

class KernelTests(TestCase):
    kernel_name = ""

    @classmethod
    def launch_kernel(cls):
        kf = KernelFinder.from_entrypoints()
        name = cls.kernel_name
        if '/' not in name:
            name = 'spec/' + name
        return kf.launch(name=name)

    @classmethod
    def setUpClass(cls):
        conn_info, km = cls.launch_kernel()
        cls.kc = BlockingKernelClient(conn_info, manager=km)
        cls.kc.wait_for_ready(timeout=TIMEOUT)
        cls.kc.allow_stdin = False

    @classmethod
    def tearDownClass(cls):
        cls.kc.shutdown_or_terminate()
        cls.kc.close()

    def _wait_for_reply(self, future, timeout=TIMEOUT):
        loop = self.kc.loop_client.ioloop
        return loop.run_sync(lambda: future, timeout=timeout)

    language_name = ""
    file_extension = ""

    def test_kernel_info(self):
        fut = self.kc.kernel_info(reply=False)
        reply = self._wait_for_reply(fut)
        validate_message(reply, 'kernel_info_reply', fut.jupyter_msg_id)

        if self.language_name:
            self.assertEqual(reply.content['language_info']['name'],
                             self.language_name)
        if self.file_extension:
            self.assertEqual(reply.content['language_info']['file_extension'],
                             self.file_extension)
            self.assertTrue(reply.content['language_info']['file_extension'].startswith("."))



    def execute_helper(self, code, timeout=TIMEOUT,
                       silent=False, store_history=True,
                       stop_on_error=True):
        output_msgs = []
        self.kc.loop_client.add_handler('iopub', output_msgs.append)
        try:
            fut = self.kc.execute(
                code=code, silent=silent, store_history=store_history,
                stop_on_error=stop_on_error, interrupt_timeout=timeout,
                reply=False,
            )
            try:
                reply = self._wait_for_reply(fut, timeout+5)
            except ErrorInKernel as e:
                reply = e.reply_msg
        finally:
            self.kc.loop_client.add_handler('iopub', output_msgs.append)

        validate_message(reply, 'execute_reply')

        busy_msg = output_msgs[0]
        validate_message(busy_msg, 'status', fut.jupyter_msg_id)
        self.assertEqual(busy_msg.content['execution_state'], 'busy')

        real_output_msgs = []   # Excluding status and execute_input

        for msg in output_msgs[1:]:
            msg_type = msg.header['msg_type']
            validate_message(msg, msg_type, fut.jupyter_msg_id)
            if msg_type == 'status':
                self.assertEqual(msg.content['execution_state'], 'idle')
            elif msg_type == 'execute_input':
                self.assertEqual(msg.content['code'], code)
            else:
                real_output_msgs.append(msg)

        return reply, real_output_msgs

    code_hello_world = ""

    def test_execute_stdout(self):
        if not self.code_hello_world:
            raise SkipTest

        reply, output_msgs = self.execute_helper(code=self.code_hello_world)

        self.assertEqual(reply.content['status'], 'ok')

        self.assertGreaterEqual(len(output_msgs), 1)
        for msg in output_msgs:
            if (msg.header['msg_type'] == 'stream') and (msg.content['name'] == 'stdout'):
                self.assertIn('hello, world', msg.content['text'])
                break
        else:
            self.assertTrue(False, "Expected one output message of type 'stream' and 'content.name'='stdout'")

    code_stderr = ""

    def test_execute_stderr(self):
        if not self.code_stderr:
            raise SkipTest

        reply, output_msgs = self.execute_helper(code=self.code_stderr)

        self.assertEqual(reply.content['status'], 'ok')

        self.assertGreaterEqual(len(output_msgs), 1)

        for msg in output_msgs:
            if (msg.header['msg_type'] == 'stream') and (msg.content['name'] == 'stderr'):
                break
        else:
            self.assertTrue(False, "Expected one output message of type 'stream' and 'content.name'='stderr'")

    completion_samples = []

    def test_completion(self):
        if not self.completion_samples:
            raise SkipTest

        for sample in self.completion_samples:
            with self.subTest(text=sample['text']):
                fut = self.kc.complete(sample['text'], reply=False)
                reply = self._wait_for_reply(fut)
                validate_message(reply, 'complete_reply', fut.jupyter_msg_id)
                if 'matches' in sample:
                    self.assertEqual(set(reply.content['matches']),
                                     set(sample['matches']))

    complete_code_samples = []
    incomplete_code_samples = []
    invalid_code_samples = []

    def check_is_complete(self, sample, status):
        fut = self.kc.is_complete(sample, reply=False)
        reply = self._wait_for_reply(fut)
        validate_message(reply, 'is_complete_reply', fut.jupyter_msg_id)
        if reply.content['status'] != status:
            msg = "For code sample\n  {!r}\nExpected {!r}, got {!r}."
            raise AssertionError(msg.format(sample, status,
                                            reply.content['status']))

    def test_is_complete(self):
        if not (self.complete_code_samples
                or self.incomplete_code_samples
                or self.invalid_code_samples):
            raise SkipTest

        with self.subTest(status="complete"):
            for sample in self.complete_code_samples:
                self.check_is_complete(sample, 'complete')

        with self.subTest(status="incomplete"):
            for sample in self.incomplete_code_samples:
                self.check_is_complete(sample, 'incomplete')

        with self.subTest(status="invalid"):
            for sample in self.invalid_code_samples:
                self.check_is_complete(sample, 'invalid')

    code_page_something = ""

    def test_pager(self):
        if not self.code_page_something:
            raise SkipTest

        reply, output_msgs = self.execute_helper(self.code_page_something)
        self.assertEqual(reply.content['status'],  'ok')
        payloads = reply.content['payload']
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]['source'], 'page')
        mimebundle = payloads[0]['data']
        self.assertIn('text/plain', mimebundle)

    code_generate_error = ""

    def test_error(self):
        if not self.code_generate_error:
            raise SkipTest

        reply, output_msgs = self.execute_helper(self.code_generate_error)
        self.assertEqual(reply.content['status'], 'error')
        self.assertEqual(len(output_msgs), 1)
        self.assertEqual(output_msgs[0].header['msg_type'], 'error')

    code_execute_result = []

    def test_execute_result(self):
        if not self.code_execute_result:
            raise SkipTest

        for sample in self.code_execute_result:
            with self.subTest(code=sample['code']):
                reply, output_msgs = self.execute_helper(sample['code'])

                self.assertEqual(reply.content['status'], 'ok')

                self.assertGreaterEqual(len(output_msgs), 1)
                self.assertEqual(output_msgs[0].header['msg_type'], 'execute_result')
                self.assertIn('text/plain', output_msgs[0].content['data'])
                self.assertEqual(output_msgs[0].content['data']['text/plain'],
                                 sample['result'])

    code_display_data = []

    def test_display_data(self):
        if not self.code_display_data:
            raise SkipTest

        for sample in self.code_display_data:
            with self.subTest(code=sample['code']):
                reply, output_msgs = self.execute_helper(sample['code'])

                self.assertEqual(reply.content['status'], 'ok')

                self.assertGreaterEqual(len(output_msgs), 1)
                self.assertEqual(output_msgs[0].header['msg_type'], 'display_data')
                self.assertIn(sample['mime'], output_msgs[0].content['data'])

    # this should match one of the values in code_execute_result
    code_history_pattern = ""
    supported_history_operations = ()

    def history_helper(self, execute_first, timeout=TIMEOUT, **histargs):
        for code in execute_first:
            reply, output_msgs = self.execute_helper(code)

        fut = self.kc.history(**histargs, reply=False)

        reply = self._wait_for_reply(fut, timeout=timeout)
        validate_message(reply, 'history_reply', fut.jupyter_msg_id)

        return reply

    def test_history(self):
        if not self.code_execute_result:
            raise SkipTest

        codes = [s['code'] for s in self.code_execute_result]
        results = [s['result'] for s in self.code_execute_result]
        n = len(codes)

        session = start = None

        with self.subTest(hist_access_type="tail"):
            if 'tail' not in self.supported_history_operations:
                raise SkipTest
            reply = self.history_helper(codes, output=False, raw=True,
                                        hist_access_type="tail", n=n)
            self.assertEqual(len(reply.content['history']), n)
            self.assertEqual(len(reply.content['history'][0]), 3)
            self.assertEqual(codes, [h[2] for h in reply.content['history']])

            session, start = reply.content['history'][0][0:2]
            with self.subTest(output=True):
                reply = self.history_helper(codes, output=True, raw=True,
                                            hist_access_type="tail", n=n)
                self.assertEqual(len(reply.content['history'][0][2]), 2)

        with self.subTest(hist_access_type="range"):
            if 'range' not in self.supported_history_operations:
                raise SkipTest
            if session is None:
                raise SkipTest
            reply = self.history_helper(codes, output=False, raw=True,
                                        hist_access_type="range",
                                        session=session, start=start,
                                        stop=start+1)
            self.assertEqual(len(reply.content['history']), 1)
            self.assertEqual(reply.content['history'][0][0], session)
            self.assertEqual(reply.content['history'][0][1], start)

        with self.subTest(hist_access_type="search"):
            if not self.code_history_pattern:
                raise SkipTest
            if 'search' not in self.supported_history_operations:
                raise SkipTest

            with self.subTest(subsearch="normal"):
                reply = self.history_helper(codes, output=False, raw=True,
                                            hist_access_type="search",
                                            pattern=self.code_history_pattern)
                self.assertGreaterEqual(len(reply.content['history']), 1)
            with self.subTest(subsearch="unique"):
                reply = self.history_helper(codes, output=False, raw=True,
                                            hist_access_type="search",
                                            pattern=self.code_history_pattern,
                                            unique=True)
                entries = [x[2] for x in reply.content['history']]
                if len(entries) > len(set(entries)):
                    raise AssertionError("History search results not unique: {}"
                                         .format(sorted(entries)))

            with self.subTest(subsearch="n"):
                reply = self.history_helper(codes, output=False, raw=True,
                                            hist_access_type="search",
                                            pattern=self.code_history_pattern,
                                            n=3)
                self.assertEqual(len(reply.content['history']), 3)

    code_inspect_sample = ""

    def test_inspect(self):
        if not self.code_inspect_sample:
            raise SkipTest

        fut = self.kc.inspect(self.code_inspect_sample, reply=False)
        reply = self._wait_for_reply(fut)
        validate_message(reply, 'inspect_reply', fut.jupyter_msg_id)

        self.assertEqual(reply.content['status'], 'ok')
        self.assertTrue(reply.content['found'])
        self.assertGreaterEqual(len(reply.content['data']), 1)

    code_clear_output = ""

    def test_clear_output(self):
        if not self.code_clear_output:
            raise SkipTest

        reply, output_msgs = self.execute_helper(code=self.code_clear_output)

        self.assertEqual(reply.content['status'], 'ok')

        self.assertGreaterEqual(len(output_msgs), 1)
        self.assertEqual(output_msgs[0].header['msg_type'], 'clear_output')
