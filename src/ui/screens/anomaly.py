from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSpinBox,
                           QDoubleSpinBox, QGroupBox, QCheckBox, QTableWidget,
                           QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import logging

logger = logging.getLogger(__name__)

class AnomalyScreen(QWidget):
    """Anomaly detection screen with detection methods and visualization."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.anomalies = None
        
        # Initialize UI
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # Update at 10Hz
        
        logger.info("AnomalyScreen initialized")

    def setup_ui(self):
        """Setup the anomaly detection screen UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Plot area
        plot_frame = QFrame()
        plot_frame.setObjectName("plotFrame")
        plot_frame.setStyleSheet("""
            QFrame#plotFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        plot_layout = QVBoxLayout(plot_frame)
        plot_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Value')
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.addLegend()
        plot_layout.addWidget(self.plot_widget)
        
        # Controls panel
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_frame.setStyleSheet("""
            QFrame#controlsFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        controls_frame.setFixedWidth(300)
        
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        
        # Detection method
        method_group = QGroupBox("Detection Method")
        method_layout = QVBoxLayout(method_group)
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Isolation Forest", "Local Outlier Factor", "Threshold"])
        method_layout.addWidget(self.method_combo)
        
        # Method parameters
        self.param_group = QGroupBox("Parameters")
        param_layout = QVBoxLayout(self.param_group)
        
        # Isolation Forest parameters
        self.if_contamination = QDoubleSpinBox()
        self.if_contamination.setMinimum(0.01)
        self.if_contamination.setMaximum(0.5)
        self.if_contamination.setValue(0.1)
        self.if_contamination.setSingleStep(0.01)
        self.if_contamination.setPrefix("Contamination: ")
        param_layout.addWidget(self.if_contamination)
        
        # LOF parameters
        self.lof_neighbors = QSpinBox()
        self.lof_neighbors.setMinimum(2)
        self.lof_neighbors.setMaximum(100)
        self.lof_neighbors.setValue(20)
        self.lof_neighbors.setPrefix("Neighbors: ")
        param_layout.addWidget(self.lof_neighbors)
        
        # Threshold parameters
        self.threshold_value = QDoubleSpinBox()
        self.threshold_value.setMinimum(-1000.0)
        self.threshold_value.setMaximum(1000.0)
        self.threshold_value.setValue(2.0)
        self.threshold_value.setSingleStep(0.1)
        self.threshold_value.setPrefix("Threshold: ")
        param_layout.addWidget(self.threshold_value)
        
        controls_layout.addWidget(method_group)
        controls_layout.addWidget(self.param_group)
        
        # Detection controls
        detect_group = QGroupBox("Controls")
        detect_layout = QVBoxLayout(detect_group)
        
        detect_btn = QPushButton("Detect Anomalies")
        detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        detect_btn.clicked.connect(self.detect_anomalies)
        detect_layout.addWidget(detect_btn)
        
        export_btn = QPushButton("Export Results")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        export_btn.clicked.connect(self.export_results)
        detect_layout.addWidget(export_btn)
        
        controls_layout.addWidget(detect_group)
        
        # Add spacer
        controls_layout.addStretch()
        
        # Add frames to content layout
        content_layout.addWidget(plot_frame)
        content_layout.addWidget(controls_frame)
        
        layout.addLayout(content_layout)

    def create_toolbar(self):
        """Create the toolbar with channel selection and controls."""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setStyleSheet("""
            QFrame#toolbar {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Channel selection
        channel_label = QLabel("Channel:")
        layout.addWidget(channel_label)
        
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Acceleration X", "Acceleration Y", "Acceleration Z",
                                   "Velocity X", "Velocity Y", "Velocity Z",
                                   "Displacement X", "Displacement Y", "Displacement Z"])
        layout.addWidget(self.channel_combo)
        
        # Add spacer
        layout.addStretch()
        
        # Control buttons
        reset_btn = QPushButton("Reset View")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(reset_btn)
        
        return toolbar

    def update_data(self):
        """Update the plot with latest data."""
        if not self.processor:
            return
            
        try:
            # Get latest data from processor
            if hasattr(self.processor, 'get_latest_data'):
                data = self.processor.get_latest_data()
                
                # Get selected channel
                channel = self.channel_combo.currentText().lower()
                
                # Update plot if data exists for selected channel
                if channel in data:
                    self.plot_widget.clear()
                    
                    # Plot data
                    self.plot_widget.plot(data[channel]['time'],
                                        data[channel]['value'],
                                        name=channel,
                                        pen='b')
                    
                    # Plot anomalies if they exist
                    if self.anomalies is not None and channel in self.anomalies:
                        anomaly_times = data[channel]['time'][self.anomalies[channel]]
                        anomaly_values = data[channel]['value'][self.anomalies[channel]]
                        self.plot_widget.plot(anomaly_times,
                                            anomaly_values,
                                            pen=None,
                                            symbol='o',
                                            symbolSize=10,
                                            symbolBrush='r',
                                            name='Anomalies')
                    
                    # Auto-range if needed
                    self.plot_widget.enableAutoRange()
        except Exception as e:
            logger.error(f"Error updating anomaly plot: {e}")

    def detect_anomalies(self):
        """Detect anomalies in the data using selected method."""
        if not self.processor:
            return
            
        try:
            # Get latest data
            data = self.processor.get_latest_data()
            channel = self.channel_combo.currentText().lower()
            
            if channel not in data:
                return
                
            # Get data values
            values = data[channel]['value']
            
            # Reshape for sklearn
            X = values.reshape(-1, 1)
            
            # Get selected method
            method = self.method_combo.currentText()
            
            # Detect anomalies
            if method == "Isolation Forest":
                clf = IsolationForest(contamination=self.if_contamination.value(),
                                    random_state=42)
                predictions = clf.fit_predict(X)
                self.anomalies = {channel: predictions == -1}
                
            elif method == "Local Outlier Factor":
                clf = LocalOutlierFactor(n_neighbors=self.lof_neighbors.value(),
                                       contamination=self.if_contamination.value())
                predictions = clf.fit_predict(X)
                self.anomalies = {channel: predictions == -1}
                
            else:  # Threshold
                threshold = self.threshold_value.value()
                self.anomalies = {channel: np.abs(values) > threshold}
                
            # Update plot
            self.update_data()
            
            # Show results
            n_anomalies = np.sum(self.anomalies[channel])
            QMessageBox.information(self, "Detection Complete",
                                  f"Found {n_anomalies} anomalies in {channel}")
            
            logger.info(f"Anomaly detection completed: {n_anomalies} anomalies found")
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            QMessageBox.critical(self, "Error", f"Failed to detect anomalies: {str(e)}")

    def export_results(self):
        """Export anomaly detection results."""
        if self.anomalies is None:
            QMessageBox.warning(self, "Warning", "No anomalies to export")
            return
            
        try:
            # Get latest data
            data = self.processor.get_latest_data()
            channel = self.channel_combo.currentText().lower()
            
            if channel not in data or channel not in self.anomalies:
                return
                
            # Create results table
            results = QTableWidget()
            results.setColumnCount(3)
            results.setHorizontalHeaderLabels(["Time", "Value", "Anomaly"])
            
            # Get anomaly indices
            anomaly_indices = np.where(self.anomalies[channel])[0]
            
            # Set row count
            results.setRowCount(len(anomaly_indices))
            
            # Fill data
            for i, idx in enumerate(anomaly_indices):
                time_item = QTableWidgetItem(f"{data[channel]['time'][idx]:.3f}")
                value_item = QTableWidgetItem(f"{data[channel]['value'][idx]:.3f}")
                anomaly_item = QTableWidgetItem("Yes")
                
                time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                anomaly_item.setTextAlignment(Qt.AlignCenter)
                
                results.setItem(i, 0, time_item)
                results.setItem(i, 1, value_item)
                results.setItem(i, 2, anomaly_item)
                
            # Resize columns
            results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            
            # Show results
            results.show()
            
            logger.info("Anomaly results exported")
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            QMessageBox.critical(self, "Error", f"Failed to export results: {str(e)}")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        event.accept() 