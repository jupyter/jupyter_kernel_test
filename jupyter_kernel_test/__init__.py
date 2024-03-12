"""Machinery for testing Jupyter kernels via the messaging protocol.
"""
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import annotations

import inspect
from queue import Empty
from typing import Any
from unittest import SkipTest, TestCase

from jupyter_client.blocking.client import BlockingKernelClient
from jupyter_client.manager import KernelManager, start_new_kernel
from jupyter_client.utils import run_sync  # type:ignore[attr-defined]

from .msgspec_v5 import validate_message

TIMEOUT = 15

__version__ = "0.7.0"


def ensure_sync(func: Any) -> Any:
    if inspect.iscoroutinefunction(func):
        return run_sync(func)
    return func


class KernelTests(TestCase):
    kernel_name = "python3"
    kc: BlockingKernelClient
    km: KernelManager

    @classmethod
    def setUpClass(cls) -> None:
        cls.km, cls.kc = start_new_kernel(kernel_name=cls.kernel_name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.kc.stop_channels()
        cls.km.shutdown_kernel()

    def flush_channels(self) -> None:
        for channel in (self.kc.shell_channel, self.kc.iopub_channel):
            while True:
                try:
                    msg = ensure_sync(channel.get_msg)(timeout=0.1)
                except TypeError:
                    msg = channel.get_msg(timeout=0.1)
                except Empty:
                    break
                else:
                    validate_message(msg)

    language_name = ""
    file_extension = ""

    def test_kernel_info(self) -> None:
        self.flush_channels()

        msg_id = self.kc.kernel_info()
        reply = self.kc.get_shell_msg(timeout=TIMEOUT)
        validate_message(reply, "kernel_info_reply", msg_id)

        if self.language_name:
            self.assertEqual(reply["content"]["language_info"]["name"], self.language_name)
        if self.file_extension:
            self.assertEqual(
                reply["content"]["language_info"]["file_extension"], self.file_extension
            )
            self.assertTrue(reply["content"]["language_info"]["file_extension"].startswith("."))

    def execute_helper(
        self,
        code: str,
        timeout: int = TIMEOUT,
        silent: bool = False,
        store_history: bool = True,
        stop_on_error: bool = True,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        msg_id = self.kc.execute(
            code=code, silent=silent, store_history=store_history, stop_on_error=stop_on_error
        )

        reply = self.get_non_kernel_info_reply(timeout=timeout)
        assert reply is not None
        validate_message(reply, "execute_reply", msg_id)

        busy_msg = ensure_sync(self.kc.iopub_channel.get_msg)(timeout=1)
        validate_message(busy_msg, "status", msg_id)
        self.assertEqual(busy_msg["content"]["execution_state"], "busy")

        output_msgs = []
        while True:
            msg = ensure_sync(self.kc.iopub_channel.get_msg)(timeout=0.1)
            validate_message(msg, msg["msg_type"], msg_id)
            if msg["msg_type"] == "status":
                self.assertEqual(msg["content"]["execution_state"], "idle")
                break
            if msg["msg_type"] == "execute_input":
                self.assertEqual(msg["content"]["code"], code)
                continue
            output_msgs.append(msg)

        return reply, output_msgs

    code_hello_world = ""

    def test_execute_stdout(self) -> None:
        if not self.code_hello_world:
            raise SkipTest("No code hello world")

        self.flush_channels()
        reply, output_msgs = self.execute_helper(code=self.code_hello_world)

        self.assertEqual(reply["content"]["status"], "ok")

        self.assertGreaterEqual(len(output_msgs), 1)
        for msg in output_msgs:
            if (msg["msg_type"] == "stream") and (msg["content"]["name"] == "stdout"):
                self.assertIn("hello, world", msg["content"]["text"])
                break
        else:
            self.assertTrue(
                False, "Expected one output message of type 'stream' and 'content.name'='stdout'"
            )

    code_stderr = ""

    def test_execute_stderr(self) -> None:
        if not self.code_stderr:
            raise SkipTest("No code stderr")

        self.flush_channels()
        reply, output_msgs = self.execute_helper(code=self.code_stderr)

        self.assertEqual(reply["content"]["status"], "ok")

        self.assertGreaterEqual(len(output_msgs), 1)

        for msg in output_msgs:
            if (msg["msg_type"] == "stream") and (msg["content"]["name"] == "stderr"):
                break
        else:
            self.assertTrue(
                False, "Expected one output message of type 'stream' and 'content.name'='stderr'"
            )

    completion_samples: list[dict[str, Any]] = []

    def get_non_kernel_info_reply(self, timeout: float | None = None) -> dict[str, Any] | None:
        while True:
            reply = self.kc.get_shell_msg(timeout=timeout)
            if reply["header"]["msg_type"] != "kernel_info_reply":
                return reply

    def test_completion(self) -> None:
        if not self.completion_samples:
            raise SkipTest("No completion samples")

        for sample in self.completion_samples:
            with self.subTest(text=sample["text"]):
                msg_id = self.kc.complete(sample["text"])
                reply = self.get_non_kernel_info_reply()
                validate_message(reply, "complete_reply", msg_id)
                assert reply is not None
                if "matches" in sample:
                    self.assertEqual(set(reply["content"]["matches"]), set(sample["matches"]))

    complete_code_samples: list[str] = []
    incomplete_code_samples: list[str] = []
    invalid_code_samples: list[str] = []

    def check_is_complete(self, sample: str, status: str) -> None:
        msg_id = self.kc.is_complete(sample)
        reply = self.get_non_kernel_info_reply()
        validate_message(reply, "is_complete_reply", msg_id)
        assert reply is not None
        if reply["content"]["status"] != status:
            msg = "For code sample\n  {!r}\nExpected {!r}, got {!r}."
            raise AssertionError(msg.format(sample, status, reply["content"]["status"]))

    def test_is_complete(self) -> None:
        if not (
            self.complete_code_samples or self.incomplete_code_samples or self.invalid_code_samples
        ):
            raise SkipTest("Not testing is_complete")

        self.flush_channels()

        with self.subTest(status="complete"):
            for sample in self.complete_code_samples:
                self.check_is_complete(sample, "complete")

        with self.subTest(status="incomplete"):
            for sample in self.incomplete_code_samples:
                self.check_is_complete(sample, "incomplete")

        with self.subTest(status="invalid"):
            for sample in self.invalid_code_samples:
                self.check_is_complete(sample, "invalid")

    code_page_something = ""

    def test_pager(self) -> None:
        if not self.code_page_something:
            raise SkipTest("No code page something")

        self.flush_channels()

        reply, output_msgs = self.execute_helper(self.code_page_something)
        self.assertEqual(reply["content"]["status"], "ok")
        payloads = reply["content"]["payload"]
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["source"], "page")
        mimebundle = payloads[0]["data"]
        self.assertIn("text/plain", mimebundle)

    code_generate_error = ""

    def test_error(self) -> None:
        if not self.code_generate_error:
            raise SkipTest("No code generate error")

        self.flush_channels()

        reply, output_msgs = self.execute_helper(self.code_generate_error)
        self.assertEqual(reply["content"]["status"], "error")
        self.assertEqual(len(output_msgs), 1)
        self.assertEqual(output_msgs[0]["msg_type"], "error")

    code_execute_result: list[dict[str, str]] = []

    def test_execute_result(self) -> None:
        if not self.code_execute_result:
            raise SkipTest("No code execute result")

        for sample in self.code_execute_result:
            with self.subTest(code=sample["code"]):
                self.flush_channels()

                reply, output_msgs = self.execute_helper(sample["code"])

                self.assertEqual(reply["content"]["status"], "ok")

                self.assertGreaterEqual(len(output_msgs), 1)

                found = False
                for msg in output_msgs:
                    if msg["msg_type"] == "execute_result":
                        found = True
                    else:
                        continue
                    mime = sample.get("mime", "text/plain")
                    self.assertIn(mime, msg["content"]["data"])
                    if "result" in sample:
                        self.assertEqual(msg["content"]["data"][mime], sample["result"])
                if not found:
                    emsg = "execute_result message not found"
                    raise AssertionError(emsg)

    code_display_data: list[dict[str, str]] = []

    def test_display_data(self) -> None:
        if not self.code_display_data:
            raise SkipTest("No code display data")

        for sample in self.code_display_data:
            with self.subTest(code=sample["code"]):
                self.flush_channels()
                reply, output_msgs = self.execute_helper(sample["code"])

                self.assertEqual(reply["content"]["status"], "ok")

                self.assertGreaterEqual(len(output_msgs), 1)
                found = False
                for msg in output_msgs:
                    if msg["msg_type"] == "display_data":
                        found = True
                    else:
                        continue
                    self.assertIn(sample["mime"], msg["content"]["data"])
                if not found:
                    emsg = "display_data message not found"
                    raise AssertionError(emsg)

    # this should match one of the values in code_execute_result
    code_history_pattern = ""
    supported_history_operations = ()

    def history_helper(
        self, execute_first: Any, timeout: float | None = TIMEOUT, **histargs: Any
    ) -> dict[str, Any]:
        self.flush_channels()

        for code in execute_first:
            self.execute_helper(code)

        self.flush_channels()
        msg_id = self.kc.history(**histargs)

        reply = self.get_non_kernel_info_reply(timeout=timeout)
        validate_message(reply, "history_reply", msg_id)
        assert reply is not None

        return reply

    def test_history(self) -> None:
        if not self.code_execute_result:
            raise SkipTest("No code execute result")

        codes = [s["code"] for s in self.code_execute_result]
        _ = [s.get("result", "") for s in self.code_execute_result]
        n = len(codes)

        session = start = None

        with self.subTest(hist_access_type="tail"):
            if "tail" not in self.supported_history_operations:
                raise SkipTest("History tail not supported")
            reply = self.history_helper(codes, output=False, raw=True, hist_access_type="tail", n=n)
            self.assertEqual(len(reply["content"]["history"]), n)
            self.assertEqual(len(reply["content"]["history"][0]), 3)
            self.assertEqual(codes, [h[2] for h in reply["content"]["history"]])

            session, start = reply["content"]["history"][0][0:2]
            with self.subTest(output=True):
                reply = self.history_helper(
                    codes, output=True, raw=True, hist_access_type="tail", n=n
                )
                self.assertEqual(len(reply["content"]["history"][0][2]), 2)

        with self.subTest(hist_access_type="range"):
            if "range" not in self.supported_history_operations:
                raise SkipTest("History range not supported")
            if session is None:
                raise SkipTest("No session")
            reply = self.history_helper(
                codes,
                output=False,
                raw=True,
                hist_access_type="range",
                session=session,
                start=start,
                stop=start + 1,
            )
            self.assertEqual(len(reply["content"]["history"]), 1)
            self.assertEqual(reply["content"]["history"][0][0], session)
            self.assertEqual(reply["content"]["history"][0][1], start)

        with self.subTest(hist_access_type="search"):
            if not self.code_history_pattern:
                raise SkipTest("No code history pattern")
            if "search" not in self.supported_history_operations:
                raise SkipTest("History search not supported")
            with self.subTest(subsearch="normal"):
                reply = self.history_helper(
                    codes,
                    output=False,
                    raw=True,
                    hist_access_type="search",
                    pattern=self.code_history_pattern,
                )
                self.assertGreaterEqual(len(reply["content"]["history"]), 1)
            with self.subTest(subsearch="unique"):
                reply = self.history_helper(
                    codes,
                    output=False,
                    raw=True,
                    hist_access_type="search",
                    pattern=self.code_history_pattern,
                    unique=True,
                )
                self.assertEqual(len(reply["content"]["history"]), 1)
            with self.subTest(subsearch="n"):
                reply = self.history_helper(
                    codes,
                    output=False,
                    raw=True,
                    hist_access_type="search",
                    pattern=self.code_history_pattern,
                    n=3,
                )
                self.assertEqual(len(reply["content"]["history"]), 3)

    code_inspect_sample = ""

    def test_inspect(self) -> None:
        if not self.code_inspect_sample:
            raise SkipTest("No code inspect sample")

        self.flush_channels()
        msg_id = self.kc.inspect(self.code_inspect_sample)
        reply = self.get_non_kernel_info_reply(timeout=TIMEOUT)
        validate_message(reply, "inspect_reply", msg_id)
        assert reply is not None
        self.assertEqual(reply["content"]["status"], "ok")
        self.assertTrue(reply["content"]["found"])
        self.assertGreaterEqual(len(reply["content"]["data"]), 1)

    code_clear_output = ""

    def test_clear_output(self) -> None:
        if not self.code_clear_output:
            raise SkipTest("No code clear output")

        self.flush_channels()
        reply, output_msgs = self.execute_helper(code=self.code_clear_output)
        self.assertEqual(reply["content"]["status"], "ok")
        self.assertGreaterEqual(len(output_msgs), 1)

        found = False
        for msg in output_msgs:
            if msg["msg_type"] == "clear_output":
                found = True
            else:
                continue
        if not found:
            emsg = "clear_output message not found"
            raise AssertionError(emsg)


class IopubWelcomeTests(TestCase):
    kernel_name = "python3"
    kc: BlockingKernelClient
    km: KernelManager

    @classmethod
    def setUpClass(cls) -> None:
        cls.km = KernelManager(kernel_name=cls.kernel_name)
        cls.km.start_kernel()
        cls.kc = cls.km.client()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.kc.stop_channels()
        cls.km.shutdown_kernel()

    support_iopub_welcome = False

    def test_recv_iopub_welcome_msg(self) -> None:
        if not self.support_iopub_welcome:
            raise SkipTest("Iopub welcome messages are not supported")

        self.kc.start_channels()
        while True:
            msg = self.kc.get_iopub_msg()
            if msg:
                self.assertEqual(msg["header"]["msg_type"], "iopub_welcome")
                self.assertEqual(msg["msg_type"], "iopub_welcome")
                self.assertEqual(
                    msg["content"]["subscription"], ""
                )  # Default: empty topic means subscription to all topics

                break
