#!/usr/bin/env python
import os, sys, unittest
from lxml import etree

BASEDIR = os.path.abspath(os.path.dirname(__file__))
TEST_FILE = os.path.join(BASEDIR, 'base.svg')
TEST_OUTPUT = os.path.join(BASEDIR, 'out.svg')

sys.path.append(os.path.join(BASEDIR, '..'))
import textext

class EffectTester(textext.TexText):
    def affect(self, args):
        self._args = args
        return textext.TexText.affect(self)
    
    def getoptions(self):
        return textext.TexText.getoptions(self, self._args)
    
    def parse(self, file=None):
        return textext.TexText.parse(self, TEST_FILE)
    
    def output(self):
        f = open(TEST_OUTPUT, 'w')
        self.document.write(TEST_OUTPUT)
        f.close()

def cmp_files(a, b):
    fa = open(a, 'r')
    fb = open(b, 'r')
    try:
        return fa.read() == fb.read()
    finally:
        fa.close()
        fb.close()

class TestConverterOutput(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        try: 
            os.chdir('/')
            os.chdir('/usr/share')
        except:
            pass

    def tearDown(self):
        os.chdir(self.cwd)

    def test_pdf2svg(self):
        test = EffectTester()
        textext.CONVERTERS = [textext.Pdf2Svg]
        test.affect(['--text=test', '-p', '', '-s', '1'])
        assert cmp_files(TEST_OUTPUT,
                         os.path.join(BASEDIR, 'out-pdf2svg.svg'))

    def test_skconvert(self):
        test = EffectTester()
        textext.CONVERTERS = [textext.SkConvert]
        test.affect(['--text=test', '-p', '', '-s', '1'])
        assert cmp_files(TEST_OUTPUT,
                         os.path.join(BASEDIR, 'out-skconvert.svg'))

    def test_plotsvg(self):
        test = EffectTester()
        textext.CONVERTERS = [textext.PstoeditPlotSvg]
        test.affect(['--text=test', '-p', '', '-s', '1'])
        assert cmp_files(TEST_OUTPUT,
                         os.path.join(BASEDIR, 'out-plotsvg.svg'))

if __name__ == "__main__":
    unittest.main()

