import logging
import os
from unittest import TestCase
from cmaker import cmaker


class Args:
    def __init__(self):
        pass


class Test(TestCase):

    def setUp(self):
        self.args = Args()
        cmaker.Logger(logging.INFO, logging.DEBUG)

    def test_parse_build(self):
        self.args.buildfile = "build.debugv.txt"
        self.args.name = "Cumulus"
        self.args.outdir = "/tmp"
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists("/tmp/CMakeLists.txt"))
        with open("/tmp/CMakeLists.txt") as f:
            self.assertIsNotNone(len(f.readlines()))

    def test_parse_build2(self):
        self.args.buildfile = "build.lcdiag.txt"
        self.args.name = "lcdiag"
        self.args.outdir = "/tmp"
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists("/tmp/CMakeLists.txt"))
        with open("/tmp/CMakeLists.txt") as f:
            self.assertIsNotNone(len(f.readlines()))

    def test_process_line(self):
        line = "arm-none-eabi-gcc ../core/qos_profiles/thor_1p.c -DDEBUG_TRACE_SIZE=0x8000 -DPLDM_FW_UPDATE"
        cmaker.process_line(line)
