from jupyter_client import KernelManager
import logging

km = KernelManager(kernel_name="julia-1.7")
logging.basicConfig()
km.log.setLevel(logging.DEBUG)
km.start_kernel()
kc = km.client()
kc.log.setLevel(logging.DEBUG)
kc.start_channels()
try:
    kc.wait_for_ready(timeout=60)
finally:
    kc.stop_channels()
    km.shutdown_kernel()

