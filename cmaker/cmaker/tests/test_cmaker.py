import logging
import os
from unittest import TestCase
from cmaker import cmaker


class Args:
    def __init__(self):
        pass


class Test(TestCase):

    def setUp(self):
        self.cmakefile = "./CMakeLists.txt"
        self.args = Args()
        self.args.outdir = "."
        cmaker.debug(logging.INFO, logging.DEBUG)
        cmaker.logfile("./cmaker.txt")

    def string_in_file(self, string: str):
        with open(self.cmakefile) as f:
            if string in f.read():
                return True
        return False

    def test_parse_build_thor(self):
        self.args.buildfile = "build.thor.txt"
        self.args.platform = "thor"
        self.args.name = "thor"
        self.args.blddir = "."
        self.args.outdir = "."
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists(self.cmakefile))
        self.assertTrue(self.string_in_file("PLDM_FW_UPDATE"))
        self.assertTrue(self.string_in_file("../RTOS/Nucleus_3/os/include"))
        self.assertTrue(self.string_in_file("../core/HWRM/hwrm_comm_nucleus.c"))

    def test_parse_build_lcdiag(self):
        self.args.buildfile = "build.lcdiag.txt"
        self.args.platform = "lcdiag"
        self.args.name = "lcdiag"
        self.args.blddir = "/git/int_nxt/main/Cumulus/drivers/diag/cdiag/build"
        self.args.outdir = "."
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists(self.cmakefile))
        self.assertTrue(self.string_in_file("CHIP_CFG=TH_A"))
        self.assertTrue(self.string_in_file(" ../../../../common/lm/include"))
        self.assertTrue(self.string_in_file(" ../device/linux/kernel/mm.c"))
        self.assertTrue(self.string_in_file(" ../tcl/generic/regcomp.c"))

    def test_parse_bnxtmt(self):
        self.args.buildfile = "build.bnxtmt.txt"
        self.args.platform = "bnxt-mt"
        self.args.name = "bnxt-mt"
        self.args.blddir = "/git/int_nxt/main/Cumulus/util/bnxt-mt/build"
        self.args.outdir = "."
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists(self.cmakefile))
        self.assertTrue(self.string_in_file("__KERNEL__"))
        self.assertTrue(self.string_in_file(" ../src/bnxtmt/tcl/unix"))
        self.assertTrue(self.string_in_file(" ../src/bnxtmt/tcl/generic/regcomp.c"))

    def test_parse_bnxt_en(self):
        self.args.buildfile = "build.bnxt_en.txt"
        self.args.platform = "bnxt_en"
        self.args.name = "bnxt_en"
        self.args.blddir = "/git/nxt-linux-drivers/v3"
        cmaker.parse_build(self.args)
        self.assertTrue(os.path.exists(self.cmakefile))
        self.assertTrue(self.string_in_file("MODULE"))
        self.assertTrue(self.string_in_file(" ../../usr/src/kernels/3.10.0-957.27.2.el7.x86_64/arch/x86/include"))
        self.assertTrue(self.string_in_file(" bnxt.c"))
