# GNU General Public License v3.0 or later (GPL-3.0-or-later)
#
# Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.

"""
Pruebas unitarias para el constructor de paquetes de Linux (build_linux_package.py).
Valida la generación de ejecutables standalone universal, la no admisión de stubs
y la integridad de los paquetes .deb y .tar.gz generados.
"""

import os
import sys
import tempfile
import unittest
import subprocess
import tarfile
import io

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import build_linux_package


class TestBuildLinuxPackage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_build_standalone_executable(self):
        """Verifica que build_standalone_executable genere un ZipApp funcional y ejecutable."""
        target_bin = os.path.join(self.temp_dir.name, "ucaba")
        build_linux_package.build_standalone_executable(target_bin)

        self.assertTrue(os.path.exists(target_bin))
        self.assertGreater(os.path.getsize(target_bin), 50000)

        with open(target_bin, "rb") as f:
            header = f.read(25)
            self.assertTrue(header.startswith(b"#!/usr/bin/env python3\n"))

        # Probar ejecucion directa via Python (simulando kernel Linux)
        test_env = {**os.environ, "UCABA_NO_UPDATE_CHECK": "1"}
        res_ver = subprocess.run([sys.executable, target_bin, "--version"], capture_output=True, text=True, env=test_env)
        self.assertEqual(res_ver.returncode, 0, f"res_ver falló con código {res_ver.returncode}: {res_ver.stderr}")
        self.assertIn("UCABA (v", res_ver.stdout)

        ejemplo_path = os.path.join(REPO_ROOT, "ejemplo.ucaba")
        if os.path.exists(ejemplo_path):
            res_run = subprocess.run([sys.executable, target_bin, "run", ejemplo_path], capture_output=True, text=True, env=test_env)
            self.assertEqual(res_run.returncode, 0, f"res_run falló con código {res_run.returncode}: stdout={res_run.stdout}, stderr={res_run.stderr}")
            self.assertIn("[RUN] Ejecutando archivo", res_run.stdout)
            self.assertNotIn("UCABA Stub Test Binary", res_run.stdout)

    def test_build_tarball_rejects_stub(self):
        """Verifica que build_tarball lance ValueError si se intenta empaquetar un stub."""
        stub_path = os.path.join(self.temp_dir.name, "fake_stub")
        with open(stub_path, "wb") as f:
            f.write(b"#!/bin/sh\necho 'UCABA Stub Test Binary'\n")

        output_tar = os.path.join(self.temp_dir.name, "out.tar.gz")
        with self.assertRaises(ValueError) as ctx:
            build_linux_package.build_tarball(stub_path, "", "", output_tar, build_linux_package.get_version())
        self.assertIn("UCABA Stub Test Binary", str(ctx.exception))

    def test_build_deb_rejects_stub(self):
        """Verifica que build_deb lance ValueError si se intenta empaquetar un stub."""
        stub_path = os.path.join(self.temp_dir.name, "fake_stub")
        with open(stub_path, "wb") as f:
            f.write(b"#!/bin/sh\necho 'UCABA Stub Test Binary'\n")

        output_deb = os.path.join(self.temp_dir.name, "out.deb")
        with self.assertRaises(ValueError) as ctx:
            build_linux_package.build_deb(stub_path, "", "", output_deb, build_linux_package.get_version())
        self.assertIn("UCABA Stub Test Binary", str(ctx.exception))

    def test_build_packages_with_valid_executable(self):
        """Verifica que tanto build_tarball como build_deb generen archivos válidos con el binario real."""
        version = build_linux_package.get_version()
        target_bin = os.path.join(self.temp_dir.name, "ucaba")
        build_linux_package.build_standalone_executable(target_bin)

        output_tar = os.path.join(self.temp_dir.name, "ucaba.tar.gz")
        build_linux_package.build_tarball(target_bin, "", "", output_tar, version)
        self.assertTrue(os.path.exists(output_tar))

        # Verificar contenido de tarball
        with tarfile.open(output_tar, "r:gz") as t:
            bin_member = next(m for m in t.getmembers() if m.name.endswith("/ucaba"))
            content = t.extractfile(bin_member).read()
            self.assertTrue(content.startswith(b"#!/usr/bin/env python3\n"))
            self.assertNotIn(b"UCABA Stub Test Binary", content)

        output_deb = os.path.join(self.temp_dir.name, "ucaba.deb")
        build_linux_package.build_deb(target_bin, "", "", output_deb, version)
        self.assertTrue(os.path.exists(output_deb))

        with open(output_deb, "rb") as f:
            deb_data = f.read()
        self.assertTrue(deb_data.startswith(b"!<arch>\n"))
        self.assertTrue(
            any(x in deb_data for x in (b"control.tar.gz", b"control.tar.xz", b"control.tar.zst")),
            "No se encontró control.tar en el paquete deb"
        )
        self.assertTrue(
            any(x in deb_data for x in (b"data.tar.gz", b"data.tar.xz", b"data.tar.zst")),
            "No se encontró data.tar en el paquete deb"
        )


if __name__ == "__main__":
    unittest.main()
