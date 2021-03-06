# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CTI
                                 A QGIS plugin
 CTI
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-09
        git sha              : $Format:%H$
        copyright            : (C) 2019 by CTI
        email                : CTI
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import sys
import processing, os
import requests
from osgeo import ogr, osr, gdal
gdal.UseExceptions()

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.utils import iface

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/libs")
import zipfile, io
from zipfile import ZipFile
from pyUFbr.baseuf import ufbr

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .CTI_dialog import CTIDialog
import os.path
import psycopg2

class CTI:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'CTI_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&CTI')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CTI', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/CTI/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'CTI'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def select_output_directory(self):
        filename = QFileDialog.getExistingDirectory(self.dlg, "Select Output Diretory ","")
        save = self.dlg.lineEdit.setText(filename)
        dist = self.dlg.doubleSpinBox.text()
        nomecurva = self.dlg.lineEdit_2.setText(filename + "/CurvasNivel.gpkg")
        nomedeclividade = self.dlg.lineEdit_4.setText(filename + "/Declividade.tif")
        nomeaspecto = self.dlg.lineEdit_5.setText(filename + "/Aspecto.tif")
        nomesombreamento = self.dlg.lineEdit_6.setText(filename + "/Sombreamento.tif")
        nomeTPI = self.dlg.lineEdit_7.setText(filename + "/TPI.tif")
        nomeTRI = self.dlg.lineEdit_8.setText(filename + "/TRI.tif")
        nomeBaciaRaster = self.dlg.lineEdit_13.setText(filename + "/BaciasHidrograficas_Raster.sdat")
        nomeCanais = self.dlg.lineEdit_15.setText(filename + "/Canais.shp")
        nomeBaciaVetor = self.dlg.lineEdit_16.setText(filename + "/BaciasHidrograficas_Vetor.shp")
        nomeJuncoes = self.dlg.lineEdit_14.setText(filename + "/Juncoes.shp")

    def atualizarCombo(self):
        Estados = self.dlg.comboBox_2.currentText()
        self.dlg.comboBox_3.clear()
        cidadesPYUFBR = self.dlg.comboBox_3.addItems(ufbr.list_cidades(Estados))

    def select_output_file1(self):
        filename_1, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo","", "*.gpkg")
        salvar_1= self.dlg.lineEdit_2.setText(filename_1)
    def select_output_file2(self):
        filename_2, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo","", "*.tif")
        salvar_2= self.dlg.lineEdit_4.setText(filename_2)
    def select_output_file3(self):
        filename_3, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.tif")
        salvar_3= self.dlg.lineEdit_5.setText(filename_3)
    def select_output_file4(self):
        filename_4, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.tif")
        salvar_4= self.dlg.lineEdit_6.setText(filename_4)
    def select_output_file5(self):
        filename_5, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.tif")
        salvar_5= self.dlg.lineEdit_7.setText(filename_5)
    def select_output_file6(self):
        filename_6, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.tif")
        salvar_6= self.dlg.lineEdit_8.setText(filename_6)
    def select_output_file7(self):
        filename_8, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.sdat")
        salvar_8= self.dlg.lineEdit_13.setText(filename_8)
    def select_output_file8(self):
        filename_9, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.shp")
        salvar_9= self.dlg.lineEdit_15.setText(filename_9)
    def select_output_file9(self):
        filename_10, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.shp")
        salvar_10= self.dlg.lineEdit_16.setText(filename_10)
    def select_output_file10(self):
        filename_11, _filter= QFileDialog.getSaveFileName(self.dlg, "Salvar arquivo ","", "*.shp")
        salvar_10= self.dlg.lineEdit_14.setText(filename_10)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&CTI'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = CTIDialog()
            self.dlg.toolButton_2.clicked.connect(self.select_output_directory)
            self.dlg.toolButton.clicked.connect(self.select_output_file1)
            self.dlg.toolButton_3.clicked.connect(self.select_output_file2)
            self.dlg.toolButton_4.clicked.connect(self.select_output_file3)
            self.dlg.toolButton_5.clicked.connect(self.select_output_file4)
            self.dlg.toolButton_6.clicked.connect(self.select_output_file5)
            self.dlg.toolButton_7.clicked.connect(self.select_output_file6)
            self.dlg.toolButton_12.clicked.connect(self.select_output_file7)
            self.dlg.toolButton_15.clicked.connect(self.select_output_file8)
            self.dlg.toolButton_14.clicked.connect(self.select_output_file9)
            self.dlg.toolButton_13.clicked.connect(self.select_output_file10)

            self.dlg.comboBox_2.currentIndexChanged.connect(self.atualizarCombo)
            self.dlg.comboBox_2.clear()
            Estados = self.dlg.comboBox_2.addItems(ufbr.list_uf)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            nomeTRI = self.dlg.lineEdit_8.text()
            nomeTPI = self.dlg.lineEdit_7.text()
            nomesombreamento = self.dlg.lineEdit_6.text()
            nomecurva = self.dlg.lineEdit_2.text()
            nomeaspecto = self.dlg.lineEdit_5.text()
            nomedeclividade = self.dlg.lineEdit_4.text()
            nomeBaciaRaster = self.dlg.lineEdit_13.text()
            nomeCanais = self.dlg.lineEdit_16.text()
            nomeBaciaVetor = self.dlg.lineEdit_15.text()
            nomeJuncoes = self.dlg.lineEdit_14.text()
            save = self.dlg.lineEdit.text()

#Importar poligono
            if self.dlg.radioButton.isChecked():
                vetor = self.dlg.qgsFileWidget.filePath()
#Utilizar Poligono da Tela
            if self.dlg.radioButton_2.isChecked():
                vetor = self.dlg.qgsMapLayerComboBox.currentLayer()
#Fazer filtragem de campo para ESTADOS/MUNICIPIOS
            if self.dlg.radioButton_3.isChecked():
                ArquivosMunicipios = os.path.dirname(__file__) + "/Arquivos_Base/MUNICIPIOS_BRASIL_5641.gpkg"
                estado = self.dlg.comboBox_2.currentText()
                municipio = self.dlg.comboBox_3.currentText()
                saidaEstado = save + "/Estado_5641" + ".gpkg"
                processing.run("native:extractbyattribute", {'INPUT':ArquivosMunicipios,'FIELD':'UF','OPERATOR':0,'VALUE':estado,'OUTPUT':saidaEstado})
                vetor = save + "/Municipio_5641" + ".gpkg"
                processing.run("native:extractbyattribute", {'INPUT':saidaEstado,'FIELD':'NM_MUNICIP','OPERATOR':0,'VALUE':municipio,'OUTPUT':vetor})
#Reprojetar poligono
            corte_reprojetado = save + "/" + "Poligono_reprojetado" + ".gpkg"
            processing.run("qgis:reprojectlayer", {'INPUT':vetor,'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:5641'),'OUTPUT': corte_reprojetado})
            layer = QgsVectorLayer(corte_reprojetado, "Limite_EPSG5641", "ogr")
            QgsProject.instance().addMapLayer(layer)
#IMPORTAR MDE
            if self.dlg.checkBox_2.isChecked():
                topodata = os.path.dirname(__file__) + "/Arquivos_Base/GRADE_TOPODATA_5641.gpkg"
                driver = ogr.GetDriverByName("ESRI Shapefile")
                dataSource = driver.Open(topodata, 0)
                poligono_limite = save + "/poligono_limite" + ".shp"
                processing.run("saga:intersect", {'A':corte_reprojetado,'B':topodata,'SPLIT':True,'RESULT':poligono_limite})
                driver = ogr.GetDriverByName("ESRI Shapefile")
                dataSource = driver.Open(poligono_limite, 0)
                poligono_limite = dataSource.GetLayer()
                for feature in poligono_limite:
                    link = feature.GetField("TOPO_URL")
                    dir1 = save + "/" + feature.GetField("TOPO_ID") + "ZN" + ".tif"
                    if not os.path.exists(dir1):
                        r = requests.get(link)
                        imagensgrade= zipfile.ZipFile(io.BytesIO(r.content)).extractall(save)

                poligono_limite_limpo = save + "/poligono_limite_limpo" + ".shp"
                poligono_limite = save + "/poligono_limite" + ".shp"
                processing.run("native:removeduplicatesbyattribute", {'INPUT':poligono_limite,'FIELDS':['fid_1'],'OUTPUT':poligono_limite_limpo})
                incrementado = save + "/incrementado" + ".shp"
                processing.run("native:addautoincrementalfield", {'INPUT':poligono_limite_limpo,'FIELD_NAME':'CONT','START':1,'GROUP_FIELDS':[],'SORT_EXPRESSION':'','SORT_ASCENDING':True,'SORT_NULLS_FIRST':False,'OUTPUT':incrementado})

                incrementado_filtrado_1 = save + "/incrementado_filtrado_1" + ".shp"
                processing.run("native:extractbyattribute", {'INPUT':incrementado,'FIELD':'CONT','OPERATOR':0,'VALUE':'1','OUTPUT':incrementado_filtrado_1})
                driver = ogr.GetDriverByName("ESRI Shapefile")
                dataSource = driver.Open(incrementado_filtrado_1, 0)
                incrementado_filtrado_1 = dataSource.GetLayer()
                for feature1 in incrementado_filtrado_1:
                    nome1 = feature1.GetField("TOPO_ID")
                    dir1 = save + "/" + nome1 + "ZN" + ".tif"
                    raster = dir1

                try:
                    incrementado_filtrado2 = save + "/incrementado_filtrado_2" + ".shp"
                    processing.run("native:extractbyattribute", {'INPUT':incrementado,'FIELD':'CONT','OPERATOR':0,'VALUE':'2','OUTPUT':incrementado_filtrado2})
                    driver = ogr.GetDriverByName("ESRI Shapefile")
                    dataSource = driver.Open(incrementado_filtrado2, 0)
                    incrementado_filtrado2 = dataSource.GetLayer()
                    for feature2 in incrementado_filtrado2:
                        nome2 = feature2.GetField("TOPO_ID")
                        dir2 = save + "/" + nome2 + "ZN" + ".tif"
                        raster1= save + "/" + "MDE_UNIDO" + ".tif"
                        processing.run("gdal:merge", {'INPUT':[raster, dir2],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT': raster1})
                        raster= raster1
                except:
                    pass

                try:
                    incrementado_filtrado3 = save + "/incrementado_filtrado_3" + ".shp"
                    processing.run("native:extractbyattribute", {'INPUT':incrementado,'FIELD':'CONT','OPERATOR':0,'VALUE':'3','OUTPUT':incrementado_filtrado3})
                    driver = ogr.GetDriverByName("ESRI Shapefile")
                    dataSource = driver.Open(incrementado_filtrado3, 0)
                    incrementado_filtrado3 = dataSource.GetLayer()
                    for feature3 in incrementado_filtrado3:
                        nome3 = feature3.GetField("TOPO_ID")
                        dir3 = save + "/" + nome3 + "ZN" + ".tif"
                        raster2= save + "/" + "MDE_UNIDO1" + ".tif"
                        processing.run("gdal:merge", {'INPUT':[raster1, dir3],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT': raster2})
                        raster= raster2
                except:
                    pass

                try:
                    incrementado_filtrado4 = save + "/incrementado_filtrado_4" + ".shp"
                    processing.run("native:extractbyattribute", {'INPUT':incrementado,'FIELD':'CONT','OPERATOR':0,'VALUE':'4','OUTPUT':incrementado_filtrado4})
                    driver = ogr.GetDriverByName("ESRI Shapefile")
                    dataSource = driver.Open(incrementado_filtrado4, 0)
                    incrementado_filtrado4 = dataSource.GetLayer()
                    for feature4 in incrementado_filtrado4:
                        nome4 = feature4.GetField("TOPO_ID")
                        dir4 = save + "/" + nome4 + "ZN" + ".tif"
                        raster3= save + "/"  + "MDE_UNIDO2" + ".tif"
                        processing.run("gdal:merge", {'INPUT':[raster2, dir4],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT': raster3})
                        raster= raster3
                except:
                    pass
#MANUAL
            if self.dlg.checkBox_3.isChecked():
                raster1 = self.dlg.qgsMapLayerComboBox_2.currentLayer()
                raster2 = self.dlg.qgsMapLayerComboBox_3.currentLayer()
                raster3 = self.dlg.qgsMapLayerComboBox_4.currentLayer()
                raster4 = self.dlg.qgsMapLayerComboBox_5.currentLayer()
                raster = save + "/" + "MDE" + ".tif"
                if self.dlg.checkBox_3.isChecked():
                    processing.run("gdal:merge", {'INPUT':[raster1, raster1],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':raster})
                if self.dlg.checkBox_3.isChecked() and self.dlg.checkBox_4.isChecked():
                    processing.run("gdal:merge", {'INPUT':[raster1, raster2],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':raster})
                if self.dlg.checkBox_3.isChecked() and self.dlg.checkBox_4.isChecked() and self.dlg.checkBox_5.isChecked():
                    processing.run("gdal:merge", {'INPUT':[raster1, raster2, raster3],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':raster})
                if self.dlg.checkBox_3.isChecked() and self.dlg.checkBox_4.isChecked() and self.dlg.checkBox_5.isChecked() and self.dlg.checkBox_6.isChecked():
                    processing.run("gdal:merge", {'INPUT':[raster1, raster2, raster3, raster4],'PCT':False,'SEPARATE':False,'NODATA_INPUT':None,'NODATA_OUTPUT':None,'OPTIONS':'','DATA_TYPE':5,'OUTPUT':raster})

#Reprojetar MDE
            MDE_reprojetado = save + "/" + "MDE_reprojetado" + ".tif"
            processing.run("gdal:warpreproject", {'INPUT':raster,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:4326'),'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:5641'),'RESAMPLING':0,'NODATA':0,'TARGET_RESOLUTION':None,'OPTIONS':'','DATA_TYPE':0,'TARGET_EXTENT':None,'TARGET_EXTENT_CRS':None,'MULTITHREADING':False,'EXTRA':'','OUTPUT':MDE_reprojetado})
# Recortar MDE
            raster = save + "MDE_Cortado" + ".tif"
            processing.run("gdal:cliprasterbymasklayer", {'INPUT':MDE_reprojetado,'MASK':corte_reprojetado,'SOURCE_CRS':QgsCoordinateReferenceSystem('5641'),'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:5641'),'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,'OUTPUT': raster})
            fileInfo = QFileInfo(raster)
            baseName = fileInfo.baseName()
            rlayer = QgsRasterLayer(raster, baseName)
            iface.addRasterLayer (raster, "MDE_Cortado")

# VETORIZAR
            if self.dlg.checkBox_7.isChecked():
                MDE_vetorizado = save + "/MDE_vetorizado.gpkg"
                processing.run("gdal:gdal2xyz", {'INPUT':raster,'BAND':1,'CSV':False,'OUTPUT':MDE_vetorizado})
                layer = QgsVectorLayer(vetorizar, 'MDE_vetorizado', "ogr")
                QgsProject.instance().addMapLayer(layer)

# CURVA DE NIVEL
            if self.dlg.checkBox_8.isChecked():
                ELEV = self.dlg.lineEdit_3.text()
                dist = self.dlg.doubleSpinBox.text()
                processing.run("gdal:contour", {'INPUT':raster,'BAND':1,'INTERVAL':dist,'FIELD_NAME':'ELEV','CREATE_3D':False,'IGNORE_NODATA':False,'NODATA':None,'OFFSET':0,'OPTIONS':'','OUTPUT':nomecurva})
                layer = QgsVectorLayer(nomecurva, 'Curva_Nivel_' + dist, "ogr")
                QgsProject.instance().addMapLayer(layer)

# ASPECTO
            if self.dlg.checkBox_13.isChecked():
                if self.dlg.checkBox_16.isChecked():
                    checkBox_16 = True
                else:
                    checkBox_16 = False
                if self.dlg.checkBox_14.isChecked():
                    checkBox_14 = True
                else:
                    checkBox_14 = False
                if self.dlg.checkBox_15.isChecked():
                    checkBox_15 = True
                else:
                    checkBox_15 = False
                processing.run("gdal:aspect", {'INPUT':raster,'BAND':1,'TRIG_ANGLE':checkBox_16,'ZERO_FLAT':False,'COMPUTE_EDGES':checkBox_14,'ZEVENBERGEN':checkBox_15,'OPTIONS':'','OUTPUT':nomeaspecto})
                fileInfo = QFileInfo(nomeaspecto)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(nomeaspecto, baseName)
                iface.addRasterLayer (nomeaspecto, "Aspecto")

# SOMBREAMENTO
            if self.dlg.checkBox_17.isChecked():
                azimute = self.dlg.spinBox.value()
                altura = self.dlg.spinBox_2.value()
                if self.dlg.checkBox_18.isChecked():
                    checkBox_18 = True
                else:
                    checkBox_18 = False
                if self.dlg.checkBox_19.isChecked():
                    checkBox_19 = True
                else:
                    checkBox_19 = False
                if self.dlg.checkBox_20.isChecked():
                    checkBox_20 = True
                else:
                    checkBox_20 = False
                if self.dlg.checkBox_21.isChecked():
                    checkBox_21 = True
                else:
                    checkBox_21 = False
                processing.run("gdal:hillshade", {'INPUT': raster,'BAND':1,'Z_FACTOR':1,'SCALE':1,'AZIMUTH':azimute,'ALTITUDE':altura,'COMPUTE_EDGES':checkBox_18,'ZEVENBERGEN':checkBox_19,'COMBINED':checkBox_20,'MULTIDIRECTIONAL':checkBox_21,'OPTIONS':'','OUTPUT':nomesombreamento})
                fileInfo = QFileInfo(nomesombreamento)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(nomesombreamento, baseName)
                iface.addRasterLayer (nomesombreamento, "Sombreamento")

# DECLIVIDADE
            if self.dlg.checkBox_9.isChecked():
                if self.dlg.checkBox_12.isChecked():
                    checkBox_12 = True
                else:
                    checkBox_12 = False
                if self.dlg.checkBox_10.isChecked():
                    checkBox_10 = True
                else:
                    checkBox_10 = False
                if self.dlg.checkBox_11.isChecked():
                    checkBox_11 = True
                else:
                    checkBox_11 = False
                processing.run("gdal:slope", {'INPUT':raster,'BAND':1,'SCALE':1,'AS_PERCENT':checkBox_12,'COMPUTE_EDGES':checkBox_10,'ZEVENBERGEN':checkBox_11,'OPTIONS':'','OUTPUT':nomedeclividade})
                fileInfo = QFileInfo(nomedeclividade)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(nomedeclividade, baseName)
                iface.addRasterLayer(nomedeclividade, 'Declividade')

# TPI
            if self.dlg.checkBox_22.isChecked():
                if self.dlg.checkBox_23.isChecked():
                    checkBox_23 = True
                else:
                    checkBox_23 = False
                processing.run("gdal:tpitopographicpositionindex", {'INPUT':raster,'BAND':1,'COMPUTE_EDGES':checkBox_23,'OPTIONS':'','OUTPUT':nomeTPI})
                fileInfo = QFileInfo(nomeTPI)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(nomeTPI, baseName)
                iface.addRasterLayer (nomeTPI, "IndicePosicaoTopografica_TPI")

# TRI
            if self.dlg.checkBox_24.isChecked():
                if self.dlg.checkBox_25.isChecked():
                    checkBox_25 = True
                else:
                    checkBox_25 = False
                processing.run("gdal:triterrainruggednessindex", {'INPUT':raster,'BAND':1,'COMPUTE_EDGES':checkBox_25,'OPTIONS':'','OUTPUT':nomeTRI})
                fileInfo = QFileInfo(nomeTRI)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(nomeTRI, baseName)
                iface.addRasterLayer (nomeTRI, "IndiceRugosidadeterreno_TRI")

# HIDROGRAFIA
            temp = 'TEMPORARY_OUTPUT'
            if self.dlg.checkBox_34.isChecked():
                checkBox_34 = nomeBaciaRaster
            else:
                checkBox_34 = temp
            if self.dlg.checkBox_31.isChecked():
                checkBox_31 = nomeCanais
            else:
                checkBox_31 = temp
            if self.dlg.checkBox_32.isChecked():
                checkBox_32 =nomeBaciaVetor
            else:
                checkBox_32 = temp
            if self.dlg.checkBox_33.isChecked():
                checkBox_33 = nomeJuncoes
            else:
                checkBox_33 = temp
            if self.dlg.checkBox_34.isChecked() or self.dlg.checkBox_32.isChecked() or self.dlg.checkBox_31.isChecked() or self.dlg.checkBox_33.isChecked():
                fillsinks = save + "/fillsinks" +  ".sdat"
                processing.run("saga:fillsinks", {'DEM':raster,'MINSLOPE':0.01,'RESULT':fillsinks})
                processing.run("saga:channelnetworkanddrainagebasins", {'DEM':fillsinks,'THRESHOLD':5,'DIRECTION':temp,'CONNECTION':temp,'ORDER':temp,'BASIN':checkBox_34,'SEGMENTS':checkBox_31,'BASINS':checkBox_32,'NODES':checkBox_33})
                fileInfo = QFileInfo(checkBox_34)
                baseName = fileInfo.baseName()
                rlayer = QgsRasterLayer(checkBox_34, baseName)
                iface.addRasterLayer (checkBox_34, "BaciasHidrograficas_Raster")
                layer = QgsVectorLayer(checkBox_31, "Canais", "ogr")
                QgsProject.instance().addMapLayer(layer)
                layer = QgsVectorLayer(checkBox_32, "BaciasHidrograficas_Vetor", "ogr")
                QgsProject.instance().addMapLayer(layer)
                layer = QgsVectorLayer(checkBox_33, "Juncoes_Rios", "ogr")
                QgsProject.instance().addMapLayer(layer)
