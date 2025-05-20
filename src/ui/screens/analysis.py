import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSlider,
                           QSpinBox, QDoubleSpinBox, QGroupBox, QDialog,
                           QListWidget, QListWidgetItem, QDialogButtonBox,
                           QInputDialog, QMessageBox, QSizePolicy, QSpacerItem,
                           QFileDialog, QTabWidget)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea
import numpy as np
import logging
from typing import Dict, List, Optional
from .realtime_plot_manager import RealtimePlotManager
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

logger = logging.getLogger(__name__)

class AnalysisScreen(QWidget):
    """Analysis screen with various analysis methods and visualization."""
    
    # Mapping từ tên hiển thị sang data_key kỹ thuật
    CHANNEL_TO_DATA_KEY = {
        "Acceleration X": "accX",
        "Acceleration Y": "accY",
        "Acceleration Z": "accZ",
        "Angular Velocity X": "gyroX",
        "Angular Velocity Y": "gyroY",
        "Angular Velocity Z": "gyroZ",
        "Angle X": "angleX",
        "Angle Y": "angleY",
        "Angle Z": "angleZ"
    }
    
    def __init__(self, processor, sensor_manager):
        super().__init__()
        self.processor = processor
        self.sensor_manager = sensor_manager
        self.current_sensor_id = None
        self.available_data_keys_for_sensor: Dict[str, str] = {}
        self.analysis_results = None
        self.results_to_plot_data = None
        
        self.setup_ui()
        
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        self.ui_update_interval = 100
        self.update_timer.start(self.ui_update_interval)
        
        self.sensor_list_check_timer = QTimer(self)
        self.sensor_list_check_timer.timeout.connect(self.update_sensor_selection_combo)
        self.sensor_list_check_timer.start(2000)
        
        logger.info("AnalysisScreen initialized.")
        self.update_sensor_selection_combo()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_layout.addWidget(QLabel("Cảm biến:"))
        self.sensor_selection_combo = QComboBox()
        self.sensor_selection_combo.setMinimumWidth(200)
        self.sensor_selection_combo.currentTextChanged.connect(self.on_sensor_selected)
        toolbar_layout.addWidget(self.sensor_selection_combo)
        
        toolbar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))

        # Analysis type selection
        toolbar_layout.addWidget(QLabel("Loại phân tích:"))
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems([
            "Phân tích thống kê",
            "Phân tích tần số",
            "Phân tích tương quan",
            "Phân tích xu hướng",
            "Anomaly Detection"
        ])
        self.analysis_type_combo.currentTextChanged.connect(self.on_analysis_type_changed)
        toolbar_layout.addWidget(self.analysis_type_combo)

        toolbar_layout.addStretch()
        main_layout.addWidget(toolbar_widget)

        # Analysis area
        self.analysis_area = DockArea()
        main_layout.addWidget(self.analysis_area)
        
        self.plot_manager = RealtimePlotManager(self.analysis_area)
        
        # Initialize analysis views
        self.setup_statistical_analysis()
        self.setup_frequency_analysis()
        self.setup_correlation_analysis()
        self.setup_trend_analysis()

    def setup_statistical_analysis(self):
        """Setup statistical analysis view."""
        stats_dock = self.plot_manager.create_plot("stats_plot", "Phân tích thống kê")
        if stats_dock:
            stats_dock.hide()  # Initially hidden

    def setup_frequency_analysis(self):
        """Setup frequency analysis view."""
        freq_dock = self.plot_manager.create_plot("freq_plot", "Phân tích tần số")
        if freq_dock:
            freq_dock.hide()  # Initially hidden

    def setup_correlation_analysis(self):
        """Setup correlation analysis view."""
        corr_dock = self.plot_manager.create_plot("corr_plot", "Phân tích tương quan")
        if corr_dock:
            corr_dock.hide()  # Initially hidden

    def setup_trend_analysis(self):
        """Setup trend analysis view."""
        trend_dock = self.plot_manager.create_plot("trend_plot", "Phân tích xu hướng")
        if trend_dock:
            trend_dock.hide()  # Initially hidden

    def update_sensor_selection_combo(self):
        if not self.sensor_manager:
            logger.warning("SensorManager not available in AnalysisScreen.")
            self.sensor_selection_combo.clear()
            self.sensor_selection_combo.setEnabled(False)
            return

        active_sensors_info = self.sensor_manager.get_all_sensor_info()
        
        current_selected_id = self.sensor_selection_combo.currentData()
        
        new_sensor_ids = {s_info['id'] for s_info in active_sensors_info}
        old_sensor_ids = {self.sensor_selection_combo.itemData(i) for i in range(self.sensor_selection_combo.count())}

        if new_sensor_ids == old_sensor_ids and len(active_sensors_info) == self.sensor_selection_combo.count():
            return

        logger.debug(f"Updating sensor selection combobox. Found {len(active_sensors_info)} sensors.")
        self.sensor_selection_combo.blockSignals(True)
        self.sensor_selection_combo.clear()
        
        if not active_sensors_info:
            self.sensor_selection_combo.addItem("Không có cảm biến nào", None)
            self.sensor_selection_combo.setEnabled(False)
            self.current_sensor_id = None
            self.available_data_keys_for_sensor.clear()
            self.plot_manager.remove_all_plots()
        else:
            self.sensor_selection_combo.setEnabled(True)
            for sensor_info_dict in active_sensors_info:
                sensor_id = sensor_info_dict['id']
                sensor_name = sensor_info_dict.get('name', sensor_id)
                self.sensor_selection_combo.addItem(f"{sensor_name} ({sensor_id})", sensor_id)
            
            if current_selected_id and current_selected_id in new_sensor_ids:
                idx = self.sensor_selection_combo.findData(current_selected_id)
                if idx != -1:
                    self.sensor_selection_combo.setCurrentIndex(idx)
                else:
                    self.sensor_selection_combo.setCurrentIndex(0)
            elif self.sensor_selection_combo.count() > 0:
                self.sensor_selection_combo.setCurrentIndex(0)
        
        self.sensor_selection_combo.blockSignals(False)
        if self.sensor_selection_combo.count() > 0 and self.sensor_selection_combo.currentData() is not None:
            self.on_sensor_selected(self.sensor_selection_combo.currentText())
        elif not active_sensors_info:
            self.on_sensor_selected("")

    def on_sensor_selected(self, selected_text: str):
        new_sensor_id = self.sensor_selection_combo.currentData()
        logger.info(f"Sensor selected in AnalysisScreen: '{selected_text}', ID: {new_sensor_id}")

        if self.current_sensor_id == new_sensor_id and new_sensor_id is not None:
            logger.debug(f"Sensor '{new_sensor_id}' already selected. No change needed.")
            return

        self.current_sensor_id = new_sensor_id
        self.available_data_keys_for_sensor.clear()

        if self.current_sensor_id and self.sensor_manager and self.processor:
            sensor_instance = self.sensor_manager.get_sensor_instance(self.current_sensor_id)
            if sensor_instance and hasattr(sensor_instance, 'get_available_data_keys'):
                data_keys_from_sensor = sensor_instance.get_available_data_keys()
                self.available_data_keys_for_sensor = {key: key for key in data_keys_from_sensor}
                logger.debug(f"Available data keys for sensor '{self.current_sensor_id}': {self.available_data_keys_for_sensor}")
            else:
                logger.warning(f"Sensor instance for '{self.current_sensor_id}' not found or has no get_available_data_keys method.")
        
        self.update_data()

    def on_analysis_type_changed(self, analysis_type: str):
        """Handle analysis type change."""
        # Hide all analysis views
        for plot_id in self.plot_manager.get_all_plot_ids():
            dock = self.plot_manager.get_dock_by_id(plot_id)
            if dock:
                dock.hide()

        # Show selected analysis view
        if analysis_type == "Phân tích thống kê":
            dock = self.plot_manager.get_dock_by_id("stats_plot")
        elif analysis_type == "Phân tích tần số":
            dock = self.plot_manager.get_dock_by_id("freq_plot")
        elif analysis_type == "Phân tích tương quan":
            dock = self.plot_manager.get_dock_by_id("corr_plot")
        elif analysis_type == "Phân tích xu hướng":
            dock = self.plot_manager.get_dock_by_id("trend_plot")
        elif analysis_type == "Anomaly Detection":
            dock = self.plot_manager.get_dock_by_id("anomaly_plot")
        
        if dock:
            dock.show()

    def update_data(self):
        """Update the plot with latest data and analysis results."""
        if not self.current_sensor_id or not self.processor:
            return

        analysis_type = self.analysis_type_combo.currentText()
        sensor_data = self.processor.get_sensor_data(self.current_sensor_id)
        
        if not sensor_data:
            return

        if analysis_type == "Phân tích thống kê":
            self.update_statistical_analysis(sensor_data)
        elif analysis_type == "Phân tích tần số":
            self.update_frequency_analysis(sensor_data)
        elif analysis_type == "Phân tích tương quan":
            self.update_correlation_analysis(sensor_data)
        elif analysis_type == "Phân tích xu hướng":
            self.update_trend_analysis(sensor_data)
        elif analysis_type == "Anomaly Detection":
            self.update_anomaly_analysis(sensor_data)

    def update_statistical_analysis(self, sensor_data: dict):
        """Update statistical analysis plots."""
        plot = self.plot_manager.get_plot_by_id("stats_plot")
        if not plot:
            return

        # Clear existing curves
        plot.clear()

        # Calculate and plot statistics for each data channel
        for data_key in self.available_data_keys_for_sensor.values():
            if data_key in sensor_data:
                data = sensor_data[data_key]
                if len(data) > 0:
                    mean = np.mean(data)
                    std = np.std(data)
                    plot.addLine(y=mean, pen='r', name=f'Mean {data_key}')
                    plot.addLine(y=mean + std, pen='g', name=f'+1σ {data_key}')
                    plot.addLine(y=mean - std, pen='g', name=f'-1σ {data_key}')

    def update_frequency_analysis(self, sensor_data: dict):
        """Update frequency analysis plots."""
        plot = self.plot_manager.get_plot_by_id("freq_plot")
        if not plot:
            return

        # Clear existing curves
        plot.clear()

        # Calculate and plot FFT for each data channel
        for data_key in self.available_data_keys_for_sensor.values():
            if data_key in sensor_data:
                data = sensor_data[data_key]
                if len(data) > 0:
                    fft = np.fft.fft(data)
                    freq = np.fft.fftfreq(len(data), d=1/100)  # Assuming 100Hz sampling rate
                    plot.plot(freq[:len(freq)//2], np.abs(fft)[:len(freq)//2], name=data_key)

    def update_correlation_analysis(self, sensor_data: dict):
        """Update correlation analysis plots."""
        plot = self.plot_manager.get_plot_by_id("corr_plot")
        if not plot:
            return

        # Clear existing curves
        plot.clear()

        # Calculate and plot correlations between data channels
        data_keys = list(self.available_data_keys_for_sensor.values())
        for i, key1 in enumerate(data_keys):
            for key2 in data_keys[i+1:]:
                if key1 in sensor_data and key2 in sensor_data:
                    data1 = sensor_data[key1]
                    data2 = sensor_data[key2]
                    if len(data1) > 0 and len(data2) > 0:
                        corr = np.correlate(data1, data2, mode='full')
                        plot.plot(corr, name=f'{key1}-{key2}')

    def update_trend_analysis(self, sensor_data: dict):
        """Update trend analysis plots."""
        plot = self.plot_manager.get_plot_by_id("trend_plot")
        if not plot:
            return

        # Clear existing curves
        plot.clear()

        # Calculate and plot trends for each data channel
        for data_key in self.available_data_keys_for_sensor.values():
            if data_key in sensor_data:
                data = sensor_data[data_key]
                if len(data) > 0:
                    x = np.arange(len(data))
                    z = np.polyfit(x, data, 1)
                    p = np.poly1d(z)
                    plot.plot(x, p(x), name=f'Trend {data_key}')

    def update_anomaly_analysis(self, sensor_data: dict):
        """Update anomaly analysis plots."""
        plot = self.plot_manager.get_plot_by_id("anomaly_plot")
        if not plot:
            return

        # Clear existing curves
        plot.clear()

        # Detect anomalies using Isolation Forest
        contamination = 0.1
        detector = IsolationForest(contamination=contamination)
        scores = detector.fit_predict(sensor_data[self.available_data_keys_for_sensor.values()].reshape(-1, 1))
        self.analysis_results = {'scores': scores}
        self.results_to_plot_data = np.where(scores == -1, sensor_data[self.available_data_keys_for_sensor.values()], np.nan)

        # Plot anomalies
        time = np.arange(len(sensor_data[self.available_data_keys_for_sensor.values()])) / self.processor.sample_rate
        plot.plot(time, self.results_to_plot_data, name='Anomalies', pen='r')

    def closeEvent(self, event):
        """Handle window close event."""
        self.update_timer.stop()
        self.sensor_list_check_timer.stop()
        super().closeEvent(event) 