from typing import Optional

import numpy as np
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMenu, QAction, QPushButton
from scipy.interpolate import interp2d
from scipy.ndimage.interpolation import zoom

from dualbandpseudocolorapp.dualbandpseudocolorrenderer import DualbandPseudocolorRenderer
from enmapbox.qgispluginsupport.qps.pyqtgraph.pyqtgraph import PlotWidget, ImageItem
from enmapbox.qgispluginsupport.qps.utils import SpatialExtent
from enmapbox.utils import BlockSignals
from enmapboxprocessing.rasterreader import RasterReader
from enmapboxprocessing.utils import Utils
from qgis.PyQt.QtWidgets import QWidget, QToolButton, QCheckBox, QMainWindow, QComboBox
from qgis.PyQt.uic import loadUi
from qgis._gui import QgsColorButton, QgsSpinBox
from qgis.core import QgsRasterLayer, QgsMapLayerProxyModel, QgsMapSettings
from qgis.gui import QgsMapCanvas, QgsRasterBandComboBox, QgsDoubleSpinBox, QgsMapLayerComboBox
from typeguard import typechecked


@typechecked
class ColorPlanePlotWidget(PlotWidget):
    def __init__(self, *args):
        PlotWidget.__init__(self, parent=None, background='#f0f0f0')
        self.setDefaultPadding(padding=0.02)


@typechecked
class DualbandPseudocolorDialog(QMainWindow):
    mLayer: QgsMapLayerComboBox
    mBand1: QgsRasterBandComboBox
    mBand2: QgsRasterBandComboBox
    mColor1: QgsColorButton
    mColor2: QgsColorButton
    mColor3: QgsColorButton
    mColor4: QgsColorButton
    mPlot: ColorPlanePlotWidget
    mMenu: QPushButton
    mMode: QComboBox
    mClasses: QgsSpinBox
    mP1: QgsDoubleSpinBox
    mP2: QgsDoubleSpinBox
    mExtent: QComboBox
    mAccuracy: QComboBox

    mLiveUpdate: QCheckBox
    mApply: QToolButton

    ContinuouseMode, EqualIntervalMode, QuantileMode = 0, 1, 2
    EstimatedAccuracy, ActualAccuracy = 0, 1
    WholeRasterExtent, CurrentCanvasExtent = 0, 1

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi(__file__.replace('.py', '.ui'), self)

        from enmapbox import EnMAPBox
        self.enmapBox = EnMAPBox.instance()
        self.colorPlane: np.ndarray

        self.mMapCanvas: Optional[QgsMapCanvas] = None
        self.mLayer.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.mP1.setClearValue(self.mP1.value())
        self.mP2.setClearValue(self.mP2.value())

        self.predefinedColorPlanes = {
            'Katja Kowalski 1': ['#0198eb', '#830050', '#bebebf', '#fee413'],
            'Joshua Stevens 1': ['#64acbe', '#574249', '#e8e8e8', '#c85a5a'],
            'Joshua Stevens 2': ['#be64ac', '#3b4994', '#e8e8e8', '#5ac8c8'],
            'Joshua Stevens 3': ['#73ae80', '#2a5a5b', '#e8e8e8', '#6c83b5'],
            'Joshua Stevens 4': ['#9972af', '#804d36', '#e8e8e8', '#c8b35a'],
        }
        menu = QMenu()
        for name in self.predefinedColorPlanes:
            menu.addAction(name, self.onColorPlaneSelected)
            # todo: make icons; see https://stackoverflow.com/questions/55394894/update-qpushbutton-icon-from-an-numpy-array-dont-work
        self.mMenu.setMenu(menu)

        self.mLayer.layerChanged.connect(self.onLayerChanged)
        self.mBand1.bandChanged.connect(self.onLiveUpdate)
        self.mBand2.bandChanged.connect(self.onLiveUpdate)
        self.mColor1.colorChanged.connect(self.onColorChanged)
        self.mColor2.colorChanged.connect(self.onColorChanged)
        self.mColor3.colorChanged.connect(self.onColorChanged)
        self.mColor4.colorChanged.connect(self.onColorChanged)
        self.mMode.currentIndexChanged.connect(self.onColorChanged)
        self.mClasses.valueChanged.connect(self.onColorChanged)
        self.mP1.valueChanged.connect(self.onLiveUpdate)
        self.mP2.valueChanged.connect(self.onLiveUpdate)
        self.mExtent.currentIndexChanged.connect(self.onLiveUpdate)
        self.mAccuracy.currentIndexChanged.connect(self.onLiveUpdate)

        self.mApply.clicked.connect(self.onApplyClicked)

        self.onColorChanged()

    def currentLayer(self) -> Optional[QgsRasterLayer]:
        return self.mLayer.currentLayer()

    def currentExtent(self) -> Optional[SpatialExtent]:
        layer = self.currentLayer()
        if layer is None:
            return None

        if self.mExtent.currentIndex() == self.WholeRasterExtent:
            return SpatialExtent(layer.crs(), layer.extent())
        elif self.mExtent.currentIndex() == self.CurrentCanvasExtent:
            mapSettings: QgsMapSettings = self.mMapCanvas.mapSettings()
            return SpatialExtent(mapSettings.destinationCrs(), self.mMapCanvas.extent()).toCrs(layer.crs())
        else:
            raise ValueError()

    def currentSampleSize(self) -> int:
        if self.mAccuracy.currentIndex() == self.EstimatedAccuracy:
            return int(QgsRasterLayer.SAMPLE_SIZE)
        elif self.mAccuracy.currentIndex() == self.ActualAccuracy:
            return 0  # use all pixel
        else:
            raise ValueError()

    def currentRenderer(self) -> Optional[DualbandPseudocolorRenderer]:
        layer = self.currentLayer()
        if layer is None:
            return None

        band1 = self.mBand1.currentBand()
        band2 = self.mBand2.currentBand()
        if -1 in [band1, band2]:
            return None

        quantile_range = self.mP1.value(), self.mP2.value()

        extent = self.currentExtent()
        extent = extent.intersect(layer.extent())
        sampleSize = self.currentSampleSize()

        reader = RasterReader(layer)
        width, height = reader.samplingWidthAndHeight(band1, extent, sampleSize)
        array = reader.array(bandList=[band1, band2], width=width, height=height, boundingBox=extent)
        maskArray = np.all(reader.maskArray(array, [band1, band2]), axis=0)
        array1, array2 = array
        values1 = array1[maskArray]
        values2 = array2[maskArray]

        if len(values1) == 0:
            return None

        min1, max1 = np.percentile(values1, quantile_range)
        min2, max2 = np.percentile(values2, quantile_range)

        mode = self.mMode.currentIndex()
        if mode in [self.ContinuouseMode, self.EqualIntervalMode]:
            binEdges1 = np.linspace(min1, max1, self.colorPlane.shape[0] + 1)
            binEdges2 = np.linspace(min2, max2, self.colorPlane.shape[1] + 1)
        else:
            binEdges1 = np.percentile(
                values1[(min1 <= values1) * (values1 <= max1)],
                np.linspace(0, 100, self.colorPlane.shape[0] + 1)
            )
            binEdges2 = np.percentile(
                values2[(min2 <= values2) * (values1 <= max2)],
                np.linspace(0, 100, self.colorPlane.shape[1] + 1)
            )

        # update plot
        ax = self.mPlot.getAxis('bottom')
        ay = self.mPlot.getAxis('left')
        if mode == self.ContinuouseMode:
            ax.setTicks([[(0, smartRound(binEdges1[0])), (len(binEdges1), smartRound(binEdges1[-1]))]])
            ay.setTicks([[(0, smartRound(binEdges2[0])), (len(binEdges2), smartRound(binEdges2[-1]))]])
        else:
            ax.setTicks([[(i, smartRound(value)) for i, value in enumerate(binEdges1)]])
            ay.setTicks([[(i, smartRound(value)) for i, value in enumerate(binEdges2)]])
        self.mPlot.setLabel(axis='bottom', text=reader.bandName(band1))
        self.mPlot.setLabel(axis='left', text=reader.bandName(band2))

        # make renderer
        renderer = DualbandPseudocolorRenderer()
        renderer.setRange(min1, min2, max1, max2)
        renderer.setBands(band1, band2)
        renderer.setColorPlane(self.colorPlane)
        renderer.setBinEdges(binEdges1, binEdges2)

        return renderer

    def onLayerChanged(self):

        # get map canvas
        self.mMapCanvas = None
        layer = self.currentLayer()
        for mapDock in self.enmapBox.dockManager().mapDocks():
            if layer in mapDock.mapCanvas().layers():
                self.mMapCanvas = mapDock.mapCanvas()
                break

        # update gui
        self.mBand1.setLayer(layer)
        self.mBand2.setLayer(layer)
        self.mBand1.setBand(-1)
        self.mBand2.setBand(-1)

        if layer is None:
            return

        renderer = layer.renderer()
        if isinstance(renderer, DualbandPseudocolorRenderer):
            self.mBand1.setBand(renderer.band1)
            self.mBand2.setBand(renderer.band2)
        else:
            self.mBand1.setBand(1)
            self.mBand2.setBand(min(2, layer.bandCount()))

    def onColorChanged(self):
        mode = self.mMode.currentIndex()

        colors = [mColor.color() for mColor in [self.mColor1, self.mColor2, self.mColor3, self.mColor4]]
        colorsEdges = np.reshape([np.array([color.red(), color.green(), color.blue()]) for color in colors], (2, 2, 3))

        if mode == self.ContinuouseMode:
            self.mClasses.setEnabled(False)
            classes = 256
        else:
            self.mClasses.setEnabled(True)
            classes = self.mClasses.value()

        x, y = np.meshgrid([1, classes], [1, classes])
        Xnew = np.linspace(1, classes, classes)
        Ynew = np.linspace(1, classes, classes)
        fRed = interp2d(x, y, colorsEdges[:,:,0], kind='linear')
        redPlane = fRed(Xnew, Ynew)
        fGreen = interp2d(x, y, colorsEdges[:,:,1], kind='linear')
        greenPlane = fGreen(Xnew, Ynew)
        fBlue = interp2d(x, y, colorsEdges[:,:,2], kind='linear')
        bluePlane = fBlue(Xnew, Ynew)
        self.colorPlane = np.transpose((redPlane, greenPlane, bluePlane), (1,2,0))

        self.mPlot.clear()

        imageItem = ImageItem()
        imageItem.setImage(
            self.colorPlane[::-1], autoHistogramRange=True, autoLevels=True, autoDownsample=True,
            axisOrder='row-major'
        )

        self.mPlot.addItem(imageItem)
        self.onApplyClicked()

    def onColorPlaneSelected(self):
        action: QAction = self.sender()
        name = action.text()
        hexcolors = self.predefinedColorPlanes[name]
        for hexcolor, mColor in zip(hexcolors, [self.mColor1, self.mColor2, self.mColor3, self.mColor4]):
            mColor.setColor(QColor(hexcolor))
        self.onColorChanged()

    def onApplyClicked(self):
        layer = self.currentLayer()
        if layer is None:
            return
        renderer = self.currentRenderer()
        if renderer is None:
            return
        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def onLiveUpdate(self):
        if self.mLiveUpdate.isChecked():
            self.onApplyClicked()


@typechecked
def smartRound(value: float) -> str:
    if abs(value) < 0.1:
        return str(round(value, 4))
    elif abs(value) < 1:
        return str(round(value, 3))
    elif abs(value) < 10:
        return str(round(value, 2))
    elif abs(value) < 100:
        return str(round(value, 1))
    else:
        return str(int(round(value, 0)))
