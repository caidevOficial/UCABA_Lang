import unittest
from pseudocode.cli import format_elapsed_time, _normalize_cli_args


class TestCliTimeFormatting(unittest.TestCase):
    def test_format_elapsed_time_ms(self):
        result = format_elapsed_time(0.03761, mode="ms")
        self.assertEqual(result, "[Tiempo total: 37.61 ms]")

    def test_format_elapsed_time_full_example(self):
        # 1 Hora, 15 Minutos, 30 Segundos, 45 Milisegundos
        # 1 * 3600 + 15 * 60 + 30 + 0.045 = 3600 + 900 + 30 + 0.045 = 4530.045
        elapsed_s = 4530.045
        result = format_elapsed_time(elapsed_s, mode="full")
        self.assertEqual(
            result,
            "[Tiempo total: 1 Hora, 15 Minutos, 30 Segundos, 45 Milisegundos]"
        )

    def test_format_elapsed_time_singular_plural(self):
        # Singular: 1 Hora, 1 Minuto, 1 Segundo, 1 Milisegundo
        elapsed_singular = 3600 + 60 + 1 + 0.001
        self.assertEqual(
            format_elapsed_time(elapsed_singular, mode="full"),
            "[Tiempo total: 1 Hora, 1 Minuto, 1 Segundo, 1 Milisegundo]"
        )

        # Plural: 2 Horas, 2 Minutos, 2 Segundos, 2 Milisegundos
        elapsed_plural = 2 * 3600 + 2 * 60 + 2 + 0.002
        self.assertEqual(
            format_elapsed_time(elapsed_plural, mode="full"),
            "[Tiempo total: 2 Horas, 2 Minutos, 2 Segundos, 2 Milisegundos]"
        )

        # Zero handling (plural in Spanish: 0 Horas, 0 Minutos, etc.)
        self.assertEqual(
            format_elapsed_time(0.0, mode="full"),
            "[Tiempo total: 0 Horas, 0 Minutos, 0 Segundos, 0 Milisegundos]"
        )

    def test_normalize_cli_args(self):
        self.assertEqual(
            _normalize_cli_args(["run", "sort.ucaba", "--time"]),
            ["run", "sort.ucaba", "--time=ms"]
        )
        self.assertEqual(
            _normalize_cli_args(["run", "sort.ucaba", "--time", "full"]),
            ["run", "sort.ucaba", "--time=full"]
        )
        self.assertEqual(
            _normalize_cli_args(["run", "sort.ucaba", "--time", "completo"]),
            ["run", "sort.ucaba", "--time=completo"]
        )
        self.assertEqual(
            _normalize_cli_args(["run", "--time", "sort.ucaba"]),
            ["run", "--time=ms", "sort.ucaba"]
        )
        self.assertEqual(
            _normalize_cli_args(["run", "--time", "full", "sort.ucaba"]),
            ["run", "--time=full", "sort.ucaba"]
        )


class TestUpdater(unittest.TestCase):
    def test_parse_version(self):
        from pseudocode.updater import parse_version
        self.assertEqual(parse_version("1.11.0"), (1, 11, 0))
        self.assertEqual(parse_version("v1.11.6"), (1, 11, 6))
        self.assertTrue(parse_version("v1.11.6") > parse_version("1.11.0"))
        self.assertFalse(parse_version("1.11.0") > parse_version("1.11.6"))

    def test_check_version_status_online_update_available(self):
        from unittest.mock import patch
        from pseudocode.updater import check_version_status
        fake_release = {"latest_version": "1.11.6", "tag_name": "v1.11.6"}
        with patch("pseudocode.updater.fetch_latest_release_online", return_value=fake_release):
            status, info = check_version_status("1.11.0", force_online=True)
            self.assertEqual(status, "UPDATE_AVAILABLE")
            self.assertEqual(info["latest_version"], "1.11.6")

    def test_check_version_status_online_up_to_date(self):
        from unittest.mock import patch
        from pseudocode.updater import check_version_status
        fake_release = {"latest_version": "1.11.6", "tag_name": "v1.11.6"}
        with patch("pseudocode.updater.fetch_latest_release_online", return_value=fake_release):
            status, info = check_version_status("1.11.6", force_online=True)
            self.assertEqual(status, "UP_TO_DATE")

    def test_check_version_status_online_network_error(self):
        from unittest.mock import patch
        from pseudocode.updater import check_version_status
        with patch("pseudocode.updater.fetch_latest_release_online", return_value=None):
            status, info = check_version_status("1.11.0", force_online=True)
            self.assertEqual(status, "NETWORK_ERROR")
            self.assertIsNone(info)


if __name__ == "__main__":
    unittest.main()

