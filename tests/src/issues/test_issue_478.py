import unittest

from enmapbox.gui.enmapboxgui import EnMAPBox
from enmapbox.testing import EnMAPBoxTestCase
from qgis.PyQt.QtWidgets import QTreeView
from qgis.core import QgsProject


class TestIssue478(EnMAPBoxTestCase):

    def test_issue478(self):
        # https://bitbucket.org/hu-geomatics/enmap-box/issues/478/visualization-of-single-band-fails
        # test if sources can be opened in a new map
        EB = EnMAPBox(load_core_apps=False, load_other_apps=False)
        from enmapbox.exampledata import enmap

        from enmapbox.testing import TestObjects
        from enmapbox.gui.datasources.manager import DataSourceManagerTreeView
        EB.addSource(enmap)
        wms = TestObjects.uriWMS()
        EB.addSource(wms)
        tv = EB.dataSourceManagerTreeView()
        self.assertIsInstance(tv, DataSourceManagerTreeView)
        for src in EB.dataSourceManager().dataSources('RASTER'):
            tv.openInMap(src, rgb=[0])
            self.assertIsInstance(tv, QTreeView)

        self.showGui(EB.ui)
        EB.close()
        QgsProject.instance().removeAllMapLayers()


if __name__ == '__main__':
    unittest.main(buffer=False)
