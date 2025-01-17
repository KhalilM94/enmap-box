# -*- coding: utf-8 -*-

"""
***************************************************************************
    __main__
    ---------------------
    Date                 : August 2017
    Copyright            : (C) 2017 by Benjamin Jakimow
    Email                : benjamin.jakimow@geo.hu-berlin.de
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
**************************************************************************
"""
import argparse
import pathlib
import site

from qgis.PyQt.QtWidgets import QApplication
from qgis.core import QgsProject, QgsApplication

site.addsitedir(pathlib.Path(__file__).parents[1])

qApp: QgsApplication = None


def exitAll(*args):
    print('## Close all windows')
    QApplication.closeAllWindows()
    QApplication.processEvents()
    print('## Quit QgsApplication')
    r = QgsApplication.quit()
    print('## QgsApplication down')
    # sys.exit(0)


def run(
        debug: bool = False,
        sources: list = None,
        load_core_apps=False,
        load_other_apps=False,
):
    """
    Starts the EnMAP-Box GUI.
    """
    qAppExists = isinstance(QgsApplication.instance(), QgsApplication)
    if not qAppExists:
        from enmapbox.testing import start_app
        start_app()
    from enmapbox import initAll
    initAll()
    from enmapbox.gui.enmapboxgui import EnMAPBox
    enmapBox = EnMAPBox(load_core_apps=load_core_apps, load_other_apps=load_other_apps)
    enmapBox.run()
    print('## EnMAP-Box started')
    if True and sources is not None:
        for source in enmapBox.addSources(sourceList=sources):
            from enmapbox.gui.datasources.datasources import SpatialDataSource
            if isinstance(source, SpatialDataSource):
                try:
                    # add as map
                    lyr = source.asMapLAyer()
                    dock = enmapBox.createDock('MAP')
                    dock.addLayers([lyr])
                except Exception as ex:
                    pass

    if not qAppExists:
        print('Execute QgsApplication')
        # enmapBox.sigClosed.connect(exitAll)
        exit_code = QgsApplication.instance().exec_()
        QgsProject.instance().removeAllMapLayers()
        return exit_code
    else:
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start the EnMAP-Box')
    parser.add_argument('-d', '--debug', required=False, help='Debug mode with more outputs', action='store_true')
    # parser.add_argument('-x', '--no_exec', required=False, help='Close EnMAP-Box if QApplication is not existent',
    #                    action='store_true')
    args = parser.parse_args()

    run(debug=args.debug, load_core_apps=True, load_other_apps=True)
    s = ""
