from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QAction, QToolBar, QStatusBar,
                           QDockWidget, QTreeWidget, QTreeWidgetItem, QStackedWidget,
                           QFrame, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
import logging

from .screens.dashboard import DashboardScreen
from .screens.realtime import RealtimeScreen
from .screens.frequency import FrequencyScreen
from .screens.spreadsheet import SpreadsheetScreen
from .screens.anomaly import AnomalyScreen
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
            ("Anomaly", "anomaly"),
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
        self.realtime = RealtimeScreen(self.processor)
        self.frequency = FrequencyScreen(self.processor)
        self.spreadsheet = SpreadsheetScreen(self.processor)
        self.anomaly = AnomalyScreen(self.processor)
        self.plugins = PluginsScreen(self.processor)
        self.settings = SettingsScreen(self.processor)
        
        # Add screens to stack
        self.content_stack.addWidget(self.dashboard)
        self.content_stack.addWidget(self.management)
        self.content_stack.addWidget(self.realtime)
        self.content_stack.addWidget(self.frequency)
        self.content_stack.addWidget(self.spreadsheet)
        self.content_stack.addWidget(self.anomaly)
        self.content_stack.addWidget(self.plugins)
        self.content_stack.addWidget(self.settings)

    def connect_signals(self):
        pass

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
        
        # Update sampling rate
        if self.processor and hasattr(self.processor, 'sample_rate'):
            rate = self.processor.sample_rate
            self.sampling_rate.setText(f"Rate: {rate:.1f} Hz")
        
        # Update timestamp
        from datetime import datetime
        self.timestamp.setText(f"Time: {datetime.now().strftime('%H:%M:%S')}")

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop any running processes
        if hasattr(self, 'processor') and self.processor:
            self.processor.stop()
        
        # Stop status update timer
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        event.accept() 