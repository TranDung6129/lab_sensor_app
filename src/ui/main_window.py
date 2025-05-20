from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QAction, QToolBar, QStatusBar,
                           QDockWidget, QTreeWidget, QTreeWidgetItem, QStackedWidget,
                           QFrame, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
import logging
import time

from .screens.dashboard import DashboardScreen
from .screens.realtime import RealtimeScreen
from .screens.frequency import FrequencyScreen
from .screens.spreadsheet import SpreadsheetScreen
from .screens.analysis import AnalysisScreen
from .screens.plugins import PluginsScreen
from .screens.settings import SettingsScreen
from .screens.sensor_management import SensorManagementScreen

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main window of the Lab Sensor Application with modern UI layout."""
    
    def __init__(self, processor, sensor_manager=None):
        super().__init__()
        self.processor = processor
        self.sensor_manager = sensor_manager
        self.config = None
        
        # Initialize UI components
        self.setup_ui()
        self.setup_status_bar()
        
        # Set window properties
        self.setWindowTitle("Lab Sensor App")
        self.setGeometry(100, 100, 1280, 800)
        
        # Initialize screens
        self.init_screens()
        
        # Connect signals
        self.connect_signals()
        
        logger.info("MainWindow initialized")

    def setup_ui(self):
        """Setup the main UI layout with header, sidebar, and main content."""
        # Create central widget and main vertical layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vlayout = QVBoxLayout(central_widget)
        main_vlayout.setContentsMargins(0, 0, 0, 0)
        main_vlayout.setSpacing(0)

        # Create header (top)
        header = self.create_header()
        main_vlayout.addWidget(header)

        # Create horizontal layout for sidebar and content
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Create sidebar
        sidebar = self.create_sidebar()
        h_layout.addWidget(sidebar)

        # Create main content area
        self.content_stack = QStackedWidget()
        h_layout.addWidget(self.content_stack)
        h_layout.setStretch(0, 1)  # Sidebar
        h_layout.setStretch(1, 4)  # Main content

        # Add horizontal layout to main vertical layout
        main_vlayout.addLayout(h_layout)

    def create_header(self):
        """Create the application header with logo and menu."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame#header {
                background-color: #2c3e50;
                color: white;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 0, 10, 0)
        
        # Logo and app name
        logo_label = QLabel("Lab Sensor App")
        logo_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(logo_label)
        
        # Add spacer
        layout.addStretch()
        
        # Add menu buttons
        menu_buttons = ["File", "View", "Tools", "Help"]
        for text in menu_buttons:
            btn = QPushButton(text)
            btn.setFlat(True)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    border: none;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
            """)
            btn.clicked.connect(lambda checked, name=text: self.on_menu_button_clicked(name))
            layout.addWidget(btn)
        
        return header

    def on_menu_button_clicked(self, name):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, f"{name} Menu", f"{name} menu clicked.")

    def create_sidebar(self):
        """Create the sidebar navigation."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #34495e;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation buttons
        nav_items = [
            ("Dashboard", "dashboard"),
            ("Management", "management"),
            ("Realtime", "realtime"),
            ("Frequency", "frequency"),
            ("Spreadsheet", "spreadsheet"),
            ("Analysis", "analysis"),
            ("Plugins", "plugins"),
            ("Settings", "settings")
        ]
        
        self.nav_buttons = []
        for idx, (text, name) in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setObjectName(f"nav_{name}")
            btn.setCheckable(True)
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    border: none;
                    text-align: left;
                    padding-left: 20px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
                QPushButton:checked {
                    background-color: #2980b9;
                }
            """)
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
            btn.clicked.connect(lambda checked, index=idx: self.switch_screen(index))
        
        # Add spacer at bottom
        layout.addStretch()
        
        return sidebar

    def setup_status_bar(self):
        """Setup the status bar with sensor info."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Sensor status
        self.sensor_status = QLabel("Sensor: Disconnected")
        status_bar.addWidget(self.sensor_status)
        
        # Sampling rate
        self.sampling_rate = QLabel("Rate: 0 Hz")
        status_bar.addWidget(self.sampling_rate)
        
        # Timestamp
        self.timestamp = QLabel("Time: --:--:--")
        status_bar.addPermanentWidget(self.timestamp)
        
        # Update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second

    def init_screens(self):
        """Initialize all screen widgets."""
        # Create screen instances
        self.dashboard = DashboardScreen(self.processor)
        self.management = SensorManagementScreen(self.sensor_manager, self.processor)
        self.realtime = RealtimeScreen(self.processor, self.sensor_manager)
        self.frequency = FrequencyScreen(self.processor, self.sensor_manager)
        self.spreadsheet = SpreadsheetScreen(self.processor)
        self.analysis = AnalysisScreen(self.processor, self.sensor_manager)
        self.plugins = PluginsScreen(self.processor)
        self.settings = SettingsScreen(self.processor)
        
        # Add screens to stack
        self.content_stack.addWidget(self.dashboard)
        self.content_stack.addWidget(self.management)
        self.content_stack.addWidget(self.realtime)
        self.content_stack.addWidget(self.frequency)
        self.content_stack.addWidget(self.spreadsheet)
        self.content_stack.addWidget(self.analysis)
        self.content_stack.addWidget(self.plugins)
        self.content_stack.addWidget(self.settings)

    def connect_signals(self):
        self.management.sensor_selected.connect(self.on_sensor_selected)

    def switch_screen(self, index):
        """Switch to the selected screen."""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.content_stack.setCurrentIndex(index)

    def update_status(self):
        """Update status bar information."""
        # Update sensor status
        if self.processor and hasattr(self.processor, 'is_connected'):
            status = "Connected" if self.processor.is_connected else "Disconnected"
            self.sensor_status.setText(f"Sensor: {status}")
        
        # Update sampling rate (FPS)
        if self.processor and hasattr(self.processor, 'get_fps'):
            fps = self.processor.get_fps()
            self.sampling_rate.setText(f"Rate: {fps:.1f} Hz")
        
        # Update timestamp
        from datetime import datetime
        self.timestamp.setText(f"Time: {datetime.now().strftime('%H:%M:%S')}")

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop status update timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        event.accept() 

    def update_plots_data(self):
        if not hasattr(self, '_last_update_time'):
            self._last_update_time = time.time()
            self._update_count = 0
            return

        current_time = time.time()
        self._update_count += 1
        
        if current_time - self._last_update_time >= 1.0:  # Every second
            update_rate = self._update_count / (current_time - self._last_update_time)
            logger.info(f"Plot update rate: {update_rate:.1f} Hz")
            self._last_update_time = current_time
            self._update_count = 0

    def on_sensor_selected(self, sensor_id: str):
        """Handle sensor selection from management screen."""
        logger.info(f"Sensor selected in MainWindow: {sensor_id}")
        
        if not sensor_id:
            logger.warning("No sensor selected")
            return

        if not self.sensor_manager:
            logger.error("Sensor manager not available")
            return

        sensor_instance = self.sensor_manager.get_sensor_instance(sensor_id)
        if not sensor_instance:
            logger.error(f"Sensor instance not found for ID: {sensor_id}")
            return

        # Update status bar
        if hasattr(self, 'sensor_status'):
            status = "Connected" if sensor_instance.connected else "Disconnected"
            self.sensor_status.setText(f"Sensor: {status}")

        # Update sampling rate if available
        if hasattr(self, 'sampling_rate') and hasattr(sensor_instance, 'sample_rate'):
            rate = sensor_instance.sample_rate
            self.sampling_rate.setText(f"Rate: {rate:.1f} Hz")

        # Notify other screens about sensor selection
        if hasattr(self, 'realtime'):
            self.realtime.on_sensor_selected(sensor_id)
        if hasattr(self, 'frequency'):
            self.frequency.on_sensor_selected(sensor_id)
        if hasattr(self, 'analysis'):
            self.analysis.on_sensor_selected(sensor_id)

    def configure_plot_curves(self, plot_id: str):
        logger.debug(f"Configuring plot {plot_id} with available keys: {self.available_data_keys_for_sensor}") 