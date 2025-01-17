import numpy as np

from enmapboxprocessing.algorithm.importprismal2balgorithm import ImportPrismaL2BAlgorithm
from enmapboxprocessing.algorithm.testcase import TestCase
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxtestdata import sensorProductsRoot, SensorProducts


class TestImportPrismaL2BAlgorithm(TestCase):

    def test(self):
        if sensorProductsRoot() is None:
            return

        alg = ImportPrismaL2BAlgorithm()
        parameters = {
            alg.P_FILE: SensorProducts.Prisma.L2B,
            alg.P_OUTPUT_SPECTRAL_CUBE: self.filename('prismaL2B_SPECTRAL.tif'),
            alg.P_OUTPUT_SPECTRAL_GEOLOCATION: self.filename('prismaL2B_SPECTRAL_GEOLOCATION.vrt'),
            alg.P_OUTPUT_SPECTRAL_GEOMETRIC: self.filename('prismaL2B_SPECTRAL_GEOMETRIC.vrt'),
            alg.P_OUTPUT_SPECTRAL_ERROR: self.filename('prismaL2B_SPECTRAL_ERROR.tif'),
            alg.P_OUTPUT_PAN_CUBE: self.filename('prismaL2B_PAN.vrt'),
            alg.P_OUTPUT_PAN_GEOLOCATION: self.filename('prismaL2B_PAN_GEOLOCATION.vrt'),
            alg.P_OUTPUT_PAN_ERROR: self.filename('prismaL2B_PAN_ERROR.vrt'),
        }
        result = self.runalg(alg, parameters)
        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).bandCount())
        self.assertAlmostEqual(3077.497, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOLOCATION]).array()), 3)

        self.assertEqual(3, RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOMETRIC]).bandCount())
        self.assertAlmostEqual(48.745, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_GEOMETRIC]).array()), 3)

        self.assertEqual(234, RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).bandCount())
        self.assertAlmostEqual(0.049, np.mean(RasterReader(result[alg.P_OUTPUT_SPECTRAL_ERROR]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).bandCount())
        self.assertAlmostEqual(22182.155, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_CUBE]).array()), 3)

        self.assertEqual(2, RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).bandCount())
        self.assertAlmostEqual(32.920, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_GEOLOCATION]).array()), 3)

        self.assertEqual(1, RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).bandCount())
        self.assertAlmostEqual(0.005, np.mean(RasterReader(result[alg.P_OUTPUT_PAN_ERROR]).array()), 3)
