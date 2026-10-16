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


if __name__ == "__main__":
    unittest.main()
