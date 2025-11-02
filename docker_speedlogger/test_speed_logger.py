import unittest
from speed_logger import run_speedtest, parse_interval
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

    def test_parse_interval_seconds(self):
        self.assertAlmostEqual(parse_interval(30), 30.0)
        self.assertAlmostEqual(parse_interval("30"), 30.0)
        self.assertAlmostEqual(parse_interval("3600s"), 3600.0)

    def test_parse_interval_minutes(self):
        self.assertAlmostEqual(parse_interval("60min"), 3600.0)
        self.assertAlmostEqual(parse_interval("2m"), 120.0)

    def test_parse_interval_hours(self):
        self.assertAlmostEqual(parse_interval("1h"), 3600.0)
        self.assertAlmostEqual(parse_interval("1.5h"), 5400.0)

    def test_parse_interval_days_weeks(self):
        self.assertAlmostEqual(parse_interval("1d"), 86400.0)
        self.assertAlmostEqual(parse_interval("1w"), 604800.0)

    def test_parse_interval_invalid(self):
        with self.assertRaises(ValueError):
            parse_interval("abc")

if __name__ == "__main__":
    unittest.main()