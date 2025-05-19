from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                           QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import logging

logger = logging.getLogger(__name__)

class DashboardScreen(QWidget):
    """Dashboard screen showing system overview and quick metrics."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        
        # Initialize UI
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Update every second
        
        logger.info("DashboardScreen initialized")

    def setup_ui(self):
        """Setup the dashboard UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        # Metrics cards row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        # Create metric cards
        self.sensor_card = self.create_metric_card("Sensors Online", "0", "sensors")
        self.fps_card = self.create_metric_card("Current FPS", "0", "fps")
        self.cpu_card = self.create_metric_card("CPU Load", "0%", "cpu")
        self.gpu_card = self.create_metric_card("GPU Load", "0%", "gpu")
        
        metrics_layout.addWidget(self.sensor_card)
        metrics_layout.addWidget(self.fps_card)
        metrics_layout.addWidget(self.cpu_card)
        metrics_layout.addWidget(self.gpu_card)
        
        layout.addLayout(metrics_layout)
        
        # Mini plots row
        plots_layout = QHBoxLayout()
        plots_layout.setSpacing(20)
        
        # Create mini plots
        self.acc_plot = self.create_mini_plot("Acceleration")
        self.vel_plot = self.create_mini_plot("Velocity")
        self.disp_plot = self.create_mini_plot("Displacement")
        
        plots_layout.addWidget(self.acc_plot)
        plots_layout.addWidget(self.vel_plot)
        plots_layout.addWidget(self.disp_plot)
        
        layout.addLayout(plots_layout)
        
        # Alerts and actions row
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Alerts table
        alerts_frame = QFrame()
        alerts_frame.setObjectName("alertsFrame")
        alerts_frame.setStyleSheet("""
            QFrame#alertsFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        alerts_layout = QVBoxLayout(alerts_frame)
        alerts_layout.setContentsMargins(10, 10, 10, 10)
        
        alerts_header = QLabel("Recent Alerts")
        alerts_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        alerts_layout.addWidget(alerts_header)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(4)
        self.alerts_table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Message"])
        self.alerts_table.horizontalHeader().setStretchLastSection(True)
        alerts_layout.addWidget(self.alerts_table)
        
        # Quick actions
        actions_frame = QFrame()
        actions_frame.setObjectName("actionsFrame")
        actions_frame.setStyleSheet("""
            QFrame#actionsFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(10, 10, 10, 10)
        
        actions_header = QLabel("Quick Actions")
        actions_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        actions_layout.addWidget(actions_header)
        
        # Action buttons
        start_btn = QPushButton("Start Recording")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        config_btn = QPushButton("Load Config")
        config_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        demo_btn = QPushButton("Open Live Demo")
        demo_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        actions_layout.addWidget(start_btn)
        actions_layout.addWidget(config_btn)
        actions_layout.addWidget(demo_btn)
        actions_layout.addStretch()
        
        # Add frames to bottom layout
        bottom_layout.addWidget(alerts_frame, 2)  # Alerts take 2/3 width
        bottom_layout.addWidget(actions_frame, 1)  # Actions take 1/3 width
        
        layout.addLayout(bottom_layout)

    def create_metric_card(self, title, value, icon_name):
        """Create a metric card with title, value and icon."""
        card = QFrame()
        card.setObjectName("metricCard")
        card.setStyleSheet("""
            QFrame#metricCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setObjectName(f"{icon_name}Value")
        value_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(value_label)
        
        return card

    def create_mini_plot(self, title):
        """Create a mini plot widget."""
        frame = QFrame()
        frame.setObjectName("plotFrame")
        frame.setStyleSheet("""
            QFrame#plotFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Plot widget
        plot = pg.PlotWidget()
        plot.setBackground('w')
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.setMinimumHeight(150)
        layout.addWidget(plot)
        
        return frame

    def update_data(self):
        """Update dashboard data."""
        # Update metrics
        if self.processor:
            # Update sensor count
            sensor_count = len(self.processor.get_active_sensors()) if hasattr(self.processor, 'get_active_sensors') else 0
            self.findChild(QLabel, "sensorsValue").setText(str(sensor_count))
            
            # Update FPS
            fps = self.processor.get_fps() if hasattr(self.processor, 'get_fps') else 0
            self.findChild(QLabel, "fpsValue").setText(f"{fps:.1f}")
            
            # Update CPU/GPU load (placeholder)
            self.findChild(QLabel, "cpuValue").setText("0%")
            self.findChild(QLabel, "gpuValue").setText("0%")
            
            # Update mini plots
            self.update_mini_plots()
            
            # Update alerts
            self.update_alerts()

    def update_mini_plots(self):
        """Update the mini plots with latest data."""
        if not self.processor:
            return
            
        try:
            # Get latest data from processor
            if hasattr(self.processor, 'get_latest_data'):
                data = self.processor.get_latest_data()
                
                # Update acceleration plot
                if 'acceleration' in data:
                    acc_plot = self.acc_plot.findChild(pg.PlotWidget)
                    acc_plot.clear()
                    acc_plot.plot(data['acceleration']['time'], 
                                data['acceleration']['value'],
                                pen='b')
                
                # Update velocity plot
                if 'velocity' in data:
                    vel_plot = self.vel_plot.findChild(pg.PlotWidget)
                    vel_plot.clear()
                    vel_plot.plot(data['velocity']['time'],
                                data['velocity']['value'],
                                pen='g')
                
                # Update displacement plot
                if 'displacement' in data:
                    disp_plot = self.disp_plot.findChild(pg.PlotWidget)
                    disp_plot.clear()
                    disp_plot.plot(data['displacement']['time'],
                                 data['displacement']['value'],
                                 pen='r')
        except Exception as e:
            logger.error(f"Error updating mini plots: {e}")

    def update_alerts(self):
        """Update the alerts table with latest alerts."""
        if not self.processor:
            return
            
        try:
            # Get latest alerts from processor
            if hasattr(self.processor, 'get_latest_alerts'):
                alerts = self.processor.get_latest_alerts()
                
                # Update table
                self.alerts_table.setRowCount(len(alerts))
                for i, alert in enumerate(alerts):
                    self.alerts_table.setItem(i, 0, QTableWidgetItem(alert['time']))
                    self.alerts_table.setItem(i, 1, QTableWidgetItem(alert['type']))
                    self.alerts_table.setItem(i, 2, QTableWidgetItem(alert['severity']))
                    self.alerts_table.setItem(i, 3, QTableWidgetItem(alert['message']))
        except Exception as e:
            logger.error(f"Error updating alerts: {e}")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        event.accept() 