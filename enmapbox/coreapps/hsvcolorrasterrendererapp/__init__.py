from enmapbox.gui.applications import EnMAPBoxApplication
from enmapbox.typeguard import typechecked
from hsvcolorrasterrendererapp.hsvcolorrasterrendererdialog import HsvColorRasterRendererDialog
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu


def enmapboxApplicationFactory(enmapBox):
    return [HsvColorRasterRendererApp(enmapBox)]


@typechecked
class HsvColorRasterRendererApp(EnMAPBoxApplication):
    def __init__(self, enmapBox, parent=None):
        super().__init__(enmapBox, parent=parent)

        self.name = HsvColorRasterRendererApp.__name__
        self.version = 'dev'
        self.licence = 'GNU GPL-3'

    @classmethod
    def icon(cls):
        return QIcon(':/images/themes/default/propertyicons/symbology.svg')

    @classmethod
    def title(cls):
        return 'HSV Color Raster Renderer'

    def menu(self, appMenu: QMenu):
        a = self.utilsAddActionInAlphanumericOrder(self.enmapbox.ui.menuToolsRasterVisualizations, self.title())
        a.triggered.connect(self.startGUI)
        return appMenu

    def startGUI(self):
        w = HsvColorRasterRendererDialog(parent=self.enmapbox.ui)
        w.show()
