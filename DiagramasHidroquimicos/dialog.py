# -*- coding: utf-8 -*-
"""
dialog.py
Diálogo principal del plugin DiagramasHidroquímicos para QGIS 3.44.
Organizado en pestañas: Datos | Piper | Gibbs | Stiff
"""
import os
import traceback
import pandas as pd

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, QWidget,
    QPushButton, QLineEdit, QFileDialog, QLabel, QComboBox, QDoubleSpinBox,
    QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSizePolicy, QProgressBar, QTextEdit, QSplitter,
)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QFont


# ===========================================================================
# Hilo de trabajo (evita bloquear la UI de QGIS)
# ===========================================================================

class WorkerThread(QThread):
    finished = pyqtSignal(object, str)   # (resultado, error_msg)
    progress = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result, '')
        except Exception:
            self.finished.emit(None, traceback.format_exc())


# ===========================================================================
# Diálogo principal
# ===========================================================================

class DiagramasDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle('Diagramas Hidroquímicos – QGIS 3.44')
        self.resize(850, 620)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        # Datos internos
        self.df_raw        = None   # DataFrame cargado del Excel
        self.meq_df        = None   # DataFrame en meq/L
        self.mmol_df       = None   # DataFrame en mmol/L
        self.piper_fig     = None   # plotly Figure Piper
        self.gibbs_fig     = None   # plotly Figure Gibbs
        self.stiff_poly    = None   # GeoDataFrame polígonos
        self.stiff_lines   = None   # GeoDataFrame líneas

        self._build_ui()

    # -----------------------------------------------------------------------
    # Construcción de la interfaz
    # -----------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Título
        title = QLabel('🌊  Diagramas Hidroquímicos')
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        title.setStyleSheet('color: #1a5276; padding: 6px;')
        main_layout.addWidget(title)

        # Pestañas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet('''
            QTabBar::tab { min-width: 120px; padding: 6px 10px; font-size: 11px; }
            QTabBar::tab:selected { background: #2e86c1; color: white; font-weight: bold; }
        ''')
        main_layout.addWidget(self.tabs)

        self.tabs.addTab(self._tab_datos(),  '📂  Datos')
        self.tabs.addTab(self._tab_piper(),  '◇  Piper')
        self.tabs.addTab(self._tab_gibbs(),  '📈  Gibbs')
        self.tabs.addTab(self._tab_stiff(),  '🗺  Stiff')

        # Barra de estado
        self.status_bar = QLabel('Listo.')
        self.status_bar.setStyleSheet('color: #555; font-size: 10px; padding: 2px 4px;')
        main_layout.addWidget(self.status_bar)

    # -------------------------------------------------------------------
    # Pestaña 1: Datos
    # -------------------------------------------------------------------

    def _tab_datos(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)

        # Grupo: Archivo Excel
        grp_file = QGroupBox('Archivo Excel')
        grp_file.setStyleSheet('QGroupBox { font-weight: bold; }')
        f_layout = QHBoxLayout(grp_file)
        self.txt_excel = QLineEdit()
        self.txt_excel.setPlaceholderText('Selecciona el archivo .xlsx …')
        self.txt_excel.setReadOnly(True)
        btn_browse = QPushButton('Buscar…')
        btn_browse.setFixedWidth(80)
        btn_browse.clicked.connect(self._browse_excel)
        f_layout.addWidget(self.txt_excel)
        f_layout.addWidget(btn_browse)
        layout.addWidget(grp_file)

        # Grupo: Mapeo de columnas
        grp_cols = QGroupBox('Mapeo de columnas')
        grp_cols.setStyleSheet('QGroupBox { font-weight: bold; }')
        form = QFormLayout(grp_cols)

        self.cmb_id  = QComboBox(); self.cmb_id.setEnabled(False)
        self.cmb_x   = QComboBox(); self.cmb_x.setEnabled(False)
        self.cmb_y   = QComboBox(); self.cmb_y.setEnabled(False)
        self.cmb_tds = QComboBox(); self.cmb_tds.setEnabled(False)
        # Iones (fijos, se mapean)
        self.ion_combos = {}
        ions = ['HCO3', 'CO3', 'SO4', 'Cl', 'Ca', 'Mg', 'Na', 'K']
        form.addRow('ID / Pozo:', self.cmb_id)
        form.addRow('X (Easting):', self.cmb_x)
        form.addRow('Y (Northing):', self.cmb_y)
        form.addRow('TDS (mg/L):', self.cmb_tds)
        for ion in ions:
            cmb = QComboBox(); cmb.setEnabled(False)
            self.ion_combos[ion] = cmb
            form.addRow(f'{ion} (mg/L):', cmb)
        # Sheet name
        self.cmb_sheet = QComboBox(); self.cmb_sheet.setEnabled(False)
        form.insertRow(0, 'Hoja Excel:', self.cmb_sheet)

        layout.addWidget(grp_cols)

        # Botón cargar
        btn_load = QPushButton('🔄  Cargar y calcular')
        btn_load.setStyleSheet(
            'QPushButton { background:#2e86c1; color:white; padding:6px 16px; '
            'border-radius:4px; font-size:12px; font-weight:bold; }'
            'QPushButton:hover { background:#1a5276; }'
        )
        btn_load.clicked.connect(self._load_data)
        layout.addWidget(btn_load, alignment=Qt.AlignRight)

        # Vista previa
        self.tbl_preview = QTableWidget()
        self.tbl_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_preview.setAlternatingRowColors(True)
        layout.addWidget(QLabel('Vista previa (meq/L):'))
        layout.addWidget(self.tbl_preview)

        return w

    # -------------------------------------------------------------------
    # Pestaña 2: Piper
    # -------------------------------------------------------------------

    def _tab_piper(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)

        info = QLabel(
            'El diagrama de Piper se genera en Plotly (HTML interactivo) o como imagen PNG.\n'
            'Primero carga y calcula los datos en la pestaña "Datos".'
        )
        info.setWordWrap(True)
        info.setStyleSheet('color:#555; font-size: 11px;')
        layout.addWidget(info)

        btn_gen = QPushButton('▶  Generar Diagrama de Piper')
        btn_gen.setStyleSheet(
            'QPushButton { background:#1e8449; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; font-weight:bold; }'
            'QPushButton:hover { background:#145a32; }'
        )
        btn_gen.clicked.connect(self._generate_piper)

        btn_exp_html = QPushButton('🌐  Exportar como HTML')
        btn_exp_html.setStyleSheet(
            'QPushButton { background:#2e86c1; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; }'
            'QPushButton:hover { background:#1a5276; }'
        )
        btn_exp_html.clicked.connect(self._export_piper_html)

        btn_exp_png = QPushButton('🖼  Exportar como PNG')
        btn_exp_png.setStyleSheet(
            'QPushButton { background:#7d3c98; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; }'
            'QPushButton:hover { background:#5b2c6f; }'
        )
        btn_exp_png.clicked.connect(self._export_piper_png)

        brow = QHBoxLayout()
        brow.addWidget(btn_gen)
        brow.addWidget(btn_exp_html)
        brow.addWidget(btn_exp_png)
        brow.addStretch()
        layout.addLayout(brow)

        self.txt_piper_log = QTextEdit()
        self.txt_piper_log.setReadOnly(True)
        self.txt_piper_log.setMaximumHeight(120)
        self.txt_piper_log.setStyleSheet('font-family: monospace; font-size: 10px;')
        layout.addWidget(QLabel('Log:'))
        layout.addWidget(self.txt_piper_log)
        layout.addStretch()
        return w

    # -------------------------------------------------------------------
    # Pestaña 3: Gibbs
    # -------------------------------------------------------------------

    def _tab_gibbs(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)

        info = QLabel(
            'El diagrama de Gibbs se genera en Plotly (HTML interactivo) o como imagen PNG.\n'
            'Primero carga y calcula los datos en la pestaña "Datos".'
        )
        info.setWordWrap(True)
        info.setStyleSheet('color:#555; font-size: 11px;')
        layout.addWidget(info)

        btn_gen = QPushButton('▶  Generar Diagrama de Gibbs')
        btn_gen.setStyleSheet(
            'QPushButton { background:#1e8449; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; font-weight:bold; }'
            'QPushButton:hover { background:#145a32; }'
        )
        btn_gen.clicked.connect(self._generate_gibbs)

        btn_exp_html = QPushButton('🌐  Exportar como HTML')
        btn_exp_html.setStyleSheet(
            'QPushButton { background:#2e86c1; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; }'
            'QPushButton:hover { background:#1a5276; }'
        )
        btn_exp_html.clicked.connect(self._export_gibbs_html)

        btn_exp_png = QPushButton('🖼  Exportar como PNG')
        btn_exp_png.setStyleSheet(
            'QPushButton { background:#7d3c98; color:white; padding:7px 18px; '
            'border-radius:4px; font-size:12px; }'
            'QPushButton:hover { background:#5b2c6f; }'
        )
        btn_exp_png.clicked.connect(self._export_gibbs_png)

        brow = QHBoxLayout()
        brow.addWidget(btn_gen)
        brow.addWidget(btn_exp_html)
        brow.addWidget(btn_exp_png)
        brow.addStretch()
        layout.addLayout(brow)

        self.txt_gibbs_log = QTextEdit()
        self.txt_gibbs_log.setReadOnly(True)
        self.txt_gibbs_log.setMaximumHeight(120)
        self.txt_gibbs_log.setStyleSheet('font-family: monospace; font-size: 10px;')
        layout.addWidget(QLabel('Log:'))
        layout.addWidget(self.txt_gibbs_log)
        layout.addStretch()
        return w

    # -------------------------------------------------------------------
    # Pestaña 4: Stiff
    # -------------------------------------------------------------------

    def _tab_stiff(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)

        info = QLabel(
            'Los polígonos de Stiff se construyen a partir de las coordenadas X/Y del Excel.\n'
            'Puedes exportar a Shapefile o GeoPackage.'
        )
        info.setWordWrap(True)
        info.setStyleSheet('color:#555; font-size: 11px;')
        layout.addWidget(info)

        # Parámetros
        grp_params = QGroupBox('Parámetros')
        grp_params.setStyleSheet('QGroupBox { font-weight: bold; }')
        p_form = QFormLayout(grp_params)

        self.spin_feh = QDoubleSpinBox()
        self.spin_feh.setRange(1, 1e8)
        self.spin_feh.setValue(900)
        self.spin_feh.setDecimals(0)
        self.spin_feh.setSingleStep(100)

        self.spin_fev = QDoubleSpinBox()
        self.spin_fev.setRange(1, 1e8)
        self.spin_fev.setValue(600)
        self.spin_fev.setDecimals(0)
        self.spin_fev.setSingleStep(100)

        self.txt_crs = QLineEdit('EPSG:32616')
        self.txt_crs.setPlaceholderText('Ej. EPSG:32618, EPSG:4326 …')

        p_form.addRow('Factor horizontal (feh):', self.spin_feh)
        p_form.addRow('Factor vertical (fev):', self.spin_fev)
        p_form.addRow('CRS del proyecto (código EPSG):', self.txt_crs)
        layout.addWidget(grp_params)

        # Botones
        btn_gen   = QPushButton('▶  Generar polígonos Stiff')
        btn_shp   = QPushButton('💾  Exportar Shapefile (.shp)')
        btn_gpkg  = QPushButton('💾  Exportar GeoPackage (.gpkg)')
        btn_load_qgis = QPushButton('🗺  Cargar capas en QGIS')

        for btn, color in [
            (btn_gen,        '#1e8449'),
            (btn_shp,        '#2e86c1'),
            (btn_gpkg,       '#2e86c1'),
            (btn_load_qgis,  '#7d3c98'),
        ]:
            btn.setStyleSheet(
                f'QPushButton {{ background:{color}; color:white; padding:6px 14px; '
                f'border-radius:4px; font-size:11px; }}'
                f'QPushButton:hover {{ opacity:0.85; }}'
            )

        btn_gen.clicked.connect(self._generate_stiff)
        btn_shp.clicked.connect(self._export_stiff_shp)
        btn_gpkg.clicked.connect(self._export_stiff_gpkg)
        btn_load_qgis.clicked.connect(self._load_stiff_in_qgis)

        brow = QHBoxLayout()
        for b in [btn_gen, btn_shp, btn_gpkg, btn_load_qgis]:
            brow.addWidget(b)
        brow.addStretch()
        layout.addLayout(brow)

        self.txt_stiff_log = QTextEdit()
        self.txt_stiff_log.setReadOnly(True)
        self.txt_stiff_log.setMaximumHeight(120)
        self.txt_stiff_log.setStyleSheet('font-family: monospace; font-size: 10px;')
        layout.addWidget(QLabel('Log:'))
        layout.addWidget(self.txt_stiff_log)
        layout.addStretch()
        return w

    # ===================================================================
    # Acciones – Datos
    # ===================================================================

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Seleccionar archivo Excel', '',
            'Excel (*.xlsx *.xls *.ods)'
        )
        if not path:
            return
        self.txt_excel.setText(path)
        try:
            xl = pd.ExcelFile(path, engine='openpyxl')
            sheets = xl.sheet_names
            self.cmb_sheet.clear()
            self.cmb_sheet.addItems(sheets)
            self.cmb_sheet.setEnabled(True)
            # Leer primera hoja para obtener columnas
            df_tmp = xl.parse(sheets[0], nrows=1)
            cols = ['(ninguna)'] + list(df_tmp.columns.astype(str))
            for cmb in ([self.cmb_id, self.cmb_x, self.cmb_y, self.cmb_tds]
                        + list(self.ion_combos.values())):
                cmb.clear()
                cmb.addItems(cols)
                cmb.setEnabled(True)
            # Autodetección heurística
            self._autodetect_columns(df_tmp.columns.astype(str).tolist())
            self._set_status(f'Archivo cargado: {os.path.basename(path)} | Hoja: {sheets[0]}')
        except Exception as e:
            QMessageBox.warning(self, 'Error al leer Excel', str(e))

    def _autodetect_columns(self, cols: list):
        """Intenta mapear columnas automáticamente por nombre aproximado."""
        col_lower = {c.lower(): c for c in cols}
        mapping = {
            'cmb_id':  ['pozo', 'id', 'well', 'muestra', 'nombre', 'station'],
            'cmb_x':   ['x', 'este', 'easting', 'longitud', 'lon', 'longitude'],
            'cmb_y':   ['y', 'norte', 'northing', 'latitud', 'lat', 'latitude'],
            'cmb_tds': ['tds', 'sdt', 'solidos', 'mineralization'],
        }
        ion_map = {
            'HCO3': ['hco3', 'bicarbonato'],
            'CO3':  ['co3', 'carbonato'],
            'SO4':  ['so4', 'sulfato'],
            'Cl':   ['cl', 'cloruro'],
            'Ca':   ['ca', 'calcio'],
            'Mg':   ['mg', 'magnesio'],
            'Na':   ['na', 'sodio'],
            'K':    ['k', 'potasio'],
        }
        for attr, candidates in mapping.items():
            cmb = getattr(self, attr)
            for c in candidates:
                if c in col_lower:
                    idx = cmb.findText(col_lower[c])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)
                        break
        for ion, candidates in ion_map.items():
            cmb = self.ion_combos[ion]
            for c in candidates:
                if c in col_lower:
                    idx = cmb.findText(col_lower[c])
                    if idx >= 0:
                        cmb.setCurrentIndex(idx)
                        break

    def _load_data(self):
        path = self.txt_excel.text().strip()
        if not path:
            QMessageBox.warning(self, 'Sin archivo', 'Selecciona un archivo Excel primero.')
            return
        sheet = self.cmb_sheet.currentText()
        try:
            df = pd.read_excel(path, sheet_name=sheet, engine='openpyxl')
        except Exception as e:
            QMessageBox.critical(self, 'Error al leer Excel', str(e))
            return

        # Renombrar columnas mapeadas
        rename = {}
        id_col  = self.cmb_id.currentText()
        x_col   = self.cmb_x.currentText()
        y_col   = self.cmb_y.currentText()
        tds_col = self.cmb_tds.currentText()

        if id_col  != '(ninguna)': rename[id_col]  = 'Pozo'
        if x_col   != '(ninguna)': rename[x_col]   = 'X'
        if y_col   != '(ninguna)': rename[y_col]   = 'Y'
        if tds_col != '(ninguna)': rename[tds_col]  = 'TDS'
        for ion, cmb in self.ion_combos.items():
            col = cmb.currentText()
            if col != '(ninguna)' and col not in rename:
                rename[col] = ion

        df = df.rename(columns=rename)
        self.df_raw = df

        # Calcular conversiones
        from .core.calculations import (
            convert_to_meq, convert_to_mmol,
            build_meq_dataframe, build_mmol_dataframe,
            to_percent, calculate_cl_ratio
        )
        try:
            df_meq  = convert_to_meq(df)
            df_mmol = convert_to_mmol(df)

            has_x = 'X' in df.columns
            has_y = 'Y' in df.columns

            meq_df = build_meq_dataframe(
                df_meq, id_col='Pozo',
                x_col='X' if has_x else None,
                y_col='Y' if has_y else None,
            )
            self.meq_df = meq_df

            mmol_df = build_mmol_dataframe(
                df_mmol, id_col='Pozo',
                tds_col='TDS' if 'TDS' in df.columns else None,
            )
            self.mmol_df = calculate_cl_ratio(mmol_df)

        except Exception as e:
            QMessageBox.critical(self, 'Error en cálicos', traceback.format_exc())
            return

        # Vista previa
        self._fill_preview(meq_df)
        self._set_status(f'Datos cargados: {len(df)} muestras.')

    def _fill_preview(self, df: pd.DataFrame):
        self.tbl_preview.clear()
        cols = list(df.columns)
        self.tbl_preview.setColumnCount(len(cols))
        self.tbl_preview.setHorizontalHeaderLabels(cols)
        self.tbl_preview.setRowCount(min(len(df), 50))
        for r in range(min(len(df), 50)):
            for c, col in enumerate(cols):
                val = df.iloc[r][col]
                item = QTableWidgetItem(
                    f'{val:.4f}' if isinstance(val, float) else str(val)
                )
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tbl_preview.setItem(r, c, item)

    # ===================================================================
    # Acciones – Piper
    # ===================================================================

    def _generate_piper(self):
        if self.meq_df is None:
            QMessageBox.warning(self, 'Sin datos', 'Primero carga los datos en la pestaña "Datos".')
            return
        from .core.calculations import to_percent
        from .diagrams.piper import transform_piper_data, create_piper_plotly
        try:
            data_pct = to_percent(self.meq_df)
            piper_data = transform_piper_data(data_pct)
            self.piper_fig = create_piper_plotly(piper_data)
            self.txt_piper_log.append('✅ Diagrama de Piper generado correctamente.')
            self.txt_piper_log.append(
                f'   Muestras: {len(self.meq_df)} | '
                f'Puntos trazados: {len(piper_data)} (×3 zonas)'
            )
            self._set_status('Diagrama de Piper generado.')
        except Exception:
            self.txt_piper_log.append('❌ Error al generar Piper:\n' + traceback.format_exc())

    def _export_piper_html(self):
        if self.piper_fig is None:
            QMessageBox.warning(self, 'Sin figura', 'Genera el diagrama de Piper primero.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar Diagrama de Piper', 'piper.html', 'HTML (*.html)'
        )
        if not path:
            return
        from .diagrams.piper import export_piper_html
        try:
            export_piper_html(self.piper_fig, path)
            self.txt_piper_log.append(f'🌐 HTML exportado: {path}')
            self._set_status(f'Piper exportado → {os.path.basename(path)}')
        except Exception:
            self.txt_piper_log.append('❌ Error al exportar HTML:\n' + traceback.format_exc())

    def _export_piper_png(self):
        """Exporta el diagrama de Piper como imagen PNG usando matplotlib."""
        if self.piper_fig is None:
            QMessageBox.warning(self, 'Sin figura', 'Genera el diagrama de Piper primero.')
            return
        # Necesitamos piper_data para el PNG; lo regeneramos desde meq_df
        if self.meq_df is None:
            QMessageBox.warning(self, 'Sin datos', 'Carga los datos en la pestaña "Datos".')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar Diagrama de Piper como PNG', 'piper.png', 'PNG (*.png)'
        )
        if not path:
            return
        from .core.calculations import to_percent
        from .diagrams.piper import transform_piper_data, export_piper_png
        try:
            data_pct = to_percent(self.meq_df)
            piper_data = transform_piper_data(data_pct)
            export_piper_png(piper_data, path, dpi=150)
            self.txt_piper_log.append(f'🖼 PNG exportado: {path}')
            self._set_status(f'Piper PNG exportado → {os.path.basename(path)}')
        except Exception:
            self.txt_piper_log.append('❌ Error al exportar PNG:\n' + traceback.format_exc())

    # ===================================================================
    # Acciones – Gibbs
    # ===================================================================

    def _generate_gibbs(self):
        if self.mmol_df is None:
            QMessageBox.warning(self, 'Sin datos', 'Primero carga los datos en la pestaña "Datos".')
            return
        if 'Tds' not in self.mmol_df.columns:
            QMessageBox.warning(self, 'Sin TDS',
                                'El diagrama de Gibbs requiere la columna TDS. '
                                'Mapea la columna TDS en la pestaña "Datos".')
            return
        from .diagrams.gibbs import create_gibbs_plotly
        try:
            self.gibbs_fig = create_gibbs_plotly(self.mmol_df)
            self.txt_gibbs_log.append('✅ Diagrama de Gibbs generado correctamente.')
            self._set_status('Diagrama de Gibbs generado.')
        except Exception:
            self.txt_gibbs_log.append('❌ Error al generar Gibbs:\n' + traceback.format_exc())

    def _export_gibbs_html(self):
        if self.gibbs_fig is None:
            QMessageBox.warning(self, 'Sin figura', 'Genera el diagrama de Gibbs primero.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar Diagrama de Gibbs', 'gibbs.html', 'HTML (*.html)'
        )
        if not path:
            return
        from .diagrams.gibbs import export_gibbs_html
        try:
            export_gibbs_html(self.gibbs_fig, path)
            self.txt_gibbs_log.append(f'🌐 HTML exportado: {path}')
            self._set_status(f'Gibbs exportado → {os.path.basename(path)}')
        except Exception:
            self.txt_gibbs_log.append('❌ Error al exportar HTML:\n' + traceback.format_exc())

    def _export_gibbs_png(self):
        """Exporta el diagrama de Gibbs como imagen PNG usando matplotlib."""
        if self.mmol_df is None:
            QMessageBox.warning(self, 'Sin datos', 'Carga los datos en la pestaña "Datos".')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar Diagrama de Gibbs como PNG', 'gibbs.png', 'PNG (*.png)'
        )
        if not path:
            return
        from .diagrams.gibbs import export_gibbs_png
        try:
            export_gibbs_png(self.mmol_df, path, dpi=150)
            self.txt_gibbs_log.append(f'🖼 PNG exportado: {path}')
            self._set_status(f'Gibbs PNG exportado → {os.path.basename(path)}')
        except Exception:
            self.txt_gibbs_log.append('❌ Error al exportar PNG:\n' + traceback.format_exc())

    # ===================================================================
    # Acciones – Stiff
    # ===================================================================

    def _build_meq_for_stiff(self):
        """Construye el DataFrame meq list con X/Y para Stiff."""
        if self.meq_df is None:
            return None
        if 'X' not in self.meq_df.columns or 'Y' not in self.meq_df.columns:
            QMessageBox.warning(
                self, 'Sin coordenadas',
                'El diagrama de Stiff requiere columnas X e Y (coordenadas).\n'
                'Verifica el mapeo en la pestaña "Datos".'
            )
            return None

        # Añadir columnas _meq si no existen (compatibilidad)
        df = self.meq_df.copy()
        for ion in ['Ca', 'Mg', 'Na', 'K', 'HCO3', 'CO3', 'SO4', 'Cl']:
            if f'{ion}_meq' not in df.columns and ion in df.columns:
                df[f'{ion}_meq'] = df[ion]
        return df

    def _generate_stiff(self):
        df = self._build_meq_for_stiff()
        if df is None:
            return
        crs = self.txt_crs.text().strip() or 'EPSG:4326'
        feh = self.spin_feh.value()
        fev = self.spin_fev.value()
        from .diagrams.stiff import crear_poligonos_stiff, crear_lineas_centrales
        try:
            self.stiff_poly  = crear_poligonos_stiff(df, feh, fev, crs)
            self.stiff_lines = crear_lineas_centrales(df, feh, fev, crs)
            self.txt_stiff_log.append(
                f'✅ Polígonos Stiff generados: {len(self.stiff_poly)} polígonos | CRS: {crs}'
            )
            self._set_status('Polígonos Stiff generados.')
        except Exception:
            self.txt_stiff_log.append('❌ Error al generar Stiff:\n' + traceback.format_exc())

    def _export_stiff_shp(self):
        if self.stiff_poly is None:
            QMessageBox.warning(self, 'Sin datos', 'Genera los polígonos Stiff primero.')
            return
        folder = QFileDialog.getExistingDirectory(self, 'Seleccionar carpeta de salida')
        if not folder:
            return
        from .diagrams.stiff import export_to_shapefile
        try:
            p, l = export_to_shapefile(self.stiff_poly, self.stiff_lines, folder)
            self.txt_stiff_log.append(f'💾 Shapefiles exportados:\n   {p}\n   {l}')
            self._set_status('Stiff → Shapefile exportado.')
        except Exception:
            self.txt_stiff_log.append('❌ Error al exportar SHP:\n' + traceback.format_exc())

    def _export_stiff_gpkg(self):
        if self.stiff_poly is None:
            QMessageBox.warning(self, 'Sin datos', 'Genera los polígonos Stiff primero.')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Guardar GeoPackage', 'stiff.gpkg', 'GeoPackage (*.gpkg)'
        )
        if not path:
            return
        from .diagrams.stiff import export_to_gpkg
        try:
            export_to_gpkg(self.stiff_poly, self.stiff_lines, path)
            self.txt_stiff_log.append(f'💾 GeoPackage exportado: {path}')
            self._set_status('Stiff → GeoPackage exportado.')
        except Exception:
            self.txt_stiff_log.append('❌ Error al exportar GPKG:\n' + traceback.format_exc())

    def _load_stiff_in_qgis(self):
        """Carga los GeoDataFrames directamente en el mapa de QGIS."""
        if self.stiff_poly is None:
            QMessageBox.warning(self, 'Sin datos', 'Genera los polígonos Stiff primero.')
            return
        import tempfile, os
        try:
            from qgis.core import QgsVectorLayer, QgsProject
            tmpdir = tempfile.mkdtemp()
            from .diagrams.stiff import export_to_gpkg
            gpkg_path = os.path.join(tmpdir, 'stiff_temp.gpkg')
            export_to_gpkg(self.stiff_poly, self.stiff_lines, gpkg_path)
            for layer_name in ['stiff_poligonos', 'stiff_lineas']:
                uri = f'{gpkg_path}|layername={layer_name}'
                lyr = QgsVectorLayer(uri, layer_name, 'ogr')
                if lyr.isValid():
                    QgsProject.instance().addMapLayer(lyr)
                    self.txt_stiff_log.append(f'🗺  Capa cargada en QGIS: {layer_name}')
                else:
                    self.txt_stiff_log.append(f'⚠️  Capa inválida: {layer_name}')
            self._set_status('Capas Stiff cargadas en QGIS.')
        except Exception:
            self.txt_stiff_log.append('❌ Error al cargar en QGIS:\n' + traceback.format_exc())

    # ===================================================================
    # Helpers
    # ===================================================================

    def _set_status(self, msg: str):
        self.status_bar.setText(f'ℹ  {msg}')
