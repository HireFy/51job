from unittest import TestCase
import ipProcess.ip as ip

class TestGet_clean_proxies(TestCase):
    def test(self):
        ip.get_proxies()
