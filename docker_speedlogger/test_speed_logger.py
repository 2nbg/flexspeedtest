import unittest
from speed_logger import run_speedtest
import threading
import http.server
import socketserver

class TestSpeedLogger(unittest.TestCase):
   
    @classmethod
    def setUpClass(cls):
        # Starte einen einfachen HTTP-Server im Hintergrund
        cls.port = 8000
        handler = http.server.SimpleHTTPRequestHandler
        cls.httpd = socketserver.TCPServer(("", cls.port), handler)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever)
        cls.server_thread.daemon = True
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.server_thread.join()

    def test_run_speedtest_local_server(self):
        # Test mit dem lokalen HTTP-Server
        host = f"http://localhost:{self.port}"
        speed = run_speedtest(host)
        # Der Werte muss float sein da Download vom lokalen Server immer möglich ist
        self.assertTrue(isinstance(speed, float))

    def test_run_speedtest_valid_host(self):
        # Test mit einer kleinen Datei von Google
        host = "https://www.google.com/robots.txt"
        speed = run_speedtest(host)
        # Der Wert kann None sein, falls kein Download möglich ist
        self.assertTrue(speed is None or isinstance(speed, float))

    def test_run_speedtest_invalid_host(self):
        # Test mit ungültigem Host
        host = "https://invalid.host.example"
        speed = run_speedtest(host)
        self.assertIsNone(speed)

if __name__ == "__main__":
    unittest.main()