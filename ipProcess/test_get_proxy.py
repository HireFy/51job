from unittest import TestCase
import ipProcess.ip as ip

class TestGet_proxy(TestCase):
    def test_get_proxy(self):
        print(ip.get_proxy())
