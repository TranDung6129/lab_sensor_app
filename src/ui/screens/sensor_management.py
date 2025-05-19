from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QLineEdit, QFormLayout, QMessageBox,
                           QGroupBox)
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class SensorManagementScreen(QWidget):
    """Screen for managing sensor connections and configurations."""
    
    def __init__(self, sensor_manager, sensor_processor):
        super().__init__()
        self.sensor_manager = sensor_manager
        self.sensor_processor = sensor_processor
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the sensor management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Add sensor section
        add_sensor_frame = QFrame()
        add_sensor_frame.setObjectName("addSensorFrame")
        add_sensor_frame.setStyleSheet("""
            QFrame#addSensorFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        add_sensor_layout = QVBoxLayout(add_sensor_frame)
        add_sensor_layout.setContentsMargins(15, 15, 15, 15)
        
        # Basic info group
        basic_info_group = QGroupBox("Basic Information")
        basic_info_layout = QFormLayout()
        
        # Sensor ID input
        self.sensor_id_input = QLineEdit()
        basic_info_layout.addRow("Sensor ID:", self.sensor_id_input)
        
        # Sensor type selection
        self.sensor_type_combo = QComboBox()
        self.sensor_type_combo.addItems(self.sensor_manager.get_available_sensor_types())
        self.sensor_type_combo.currentTextChanged.connect(self.update_config_fields)
        basic_info_layout.addRow("Sensor Type:", self.sensor_type_combo)
        
        basic_info_group.setLayout(basic_info_layout)
        add_sensor_layout.addWidget(basic_info_group)
        
        # Config group
        self.config_group = QGroupBox("Configuration")
        self.config_layout = QFormLayout()
        self.config_group.setLayout(self.config_layout)
        add_sensor_layout.addWidget(self.config_group)
        
        # Initialize config fields
        self.update_config_fields()
        
        # Add button
        add_btn = QPushButton("Add Sensor")
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_sensor)
        add_sensor_layout.addWidget(add_btn)
        
        layout.addWidget(add_sensor_frame)
        
        # Active sensors table
        sensors_frame = QFrame()
        sensors_frame.setObjectName("sensorsFrame")
        sensors_frame.setStyleSheet("""
            QFrame#sensorsFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        
        sensors_layout = QVBoxLayout(sensors_frame)
        sensors_layout.setContentsMargins(15, 15, 15, 15)
        
        sensors_header = QLabel("Active Sensors")
        sensors_header.setStyleSheet("font-size: 14px; font-weight: bold;")
        sensors_layout.addWidget(sensors_header)
        
        self.sensors_table = QTableWidget()
        self.sensors_table.setColumnCount(5)
        self.sensors_table.setHorizontalHeaderLabels(["Sensor ID", "Type", "Status", "Last Data", "Actions"])
        self.sensors_table.horizontalHeader().setStretchLastSection(True)
        sensors_layout.addWidget(self.sensors_table)
        
        layout.addWidget(sensors_frame)
        
        # Update sensors table
        self.update_sensors_table()
        
    def update_config_fields(self):
        """Update configuration fields based on selected sensor type."""
        # Clear existing fields
        while self.config_layout.count():
            item = self.config_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        sensor_type = self.sensor_type_combo.currentText()
        
        # Add common fields
        self.port_input = QLineEdit()
        self.config_layout.addRow("Port:", self.port_input)
        
        self.baudrate_input = QLineEdit()
        self.baudrate_input.setText("9600")
        self.config_layout.addRow("Baudrate:", self.baudrate_input)
        
        # Add type-specific fields
        if sensor_type == "accelerometer":
            self.range_input = QLineEdit()
            self.range_input.setText("±2g")
            self.config_layout.addRow("Range:", self.range_input)
            
        elif sensor_type == "temperature":
            self.unit_input = QComboBox()
            self.unit_input.addItems(["Celsius", "Fahrenheit"])
            self.config_layout.addRow("Unit:", self.unit_input)
            
    def add_sensor(self):
        """Add a new sensor."""
        sensor_id = self.sensor_id_input.text().strip()
        sensor_type = self.sensor_type_combo.currentText()
        
        if not sensor_id:
            QMessageBox.warning(self, "Error", "Please enter a sensor ID")
            return
            
        # Create config based on sensor type
        config = {
            "port": self.port_input.text().strip(),
            "baudrate": int(self.baudrate_input.text())
        }
        
        # Add type-specific config
        if sensor_type == "accelerometer":
            config["range"] = self.range_input.text()
        elif sensor_type == "temperature":
            config["unit"] = self.unit_input.currentText()
            
        # Add sensor to manager
        if self.sensor_manager.add_sensor(sensor_id, sensor_type, config):
            # Add to processor
            self.sensor_processor.add_sensor(sensor_id, {"type": sensor_type, "config": config})
            self.update_sensors_table()
            self.clear_inputs()
        else:
            QMessageBox.warning(self, "Error", "Failed to add sensor")
            
    def remove_sensor(self, sensor_id: str):
        """Remove a sensor."""
        if self.sensor_manager.remove_sensor(sensor_id):
            self.sensor_processor.remove_sensor(sensor_id)
            self.update_sensors_table()
        else:
            QMessageBox.warning(self, "Error", f"Failed to remove sensor {sensor_id}")
            
    def update_sensors_table(self):
        """Update the sensors table with current data."""
        self.sensors_table.setRowCount(0)
        
        for sensor_id, sensor in self.sensor_manager.sensors.items():
            row = self.sensors_table.rowCount()
            self.sensors_table.insertRow(row)
            
            # Sensor ID
            self.sensors_table.setItem(row, 0, QTableWidgetItem(sensor_id))
            
            # Type
            self.sensors_table.setItem(row, 1, QTableWidgetItem(sensor.get_sensor_type()))
            
            # Status
            status = "Connected" if sensor.connected else "Disconnected"
            self.sensors_table.setItem(row, 2, QTableWidgetItem(status))
            
            # Last Data
            last_data = str(sensor.last_data) if sensor.last_data else "No data"
            self.sensors_table.setItem(row, 3, QTableWidgetItem(last_data))
            
            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            remove_btn.clicked.connect(lambda checked, sid=sensor_id: self.remove_sensor(sid))
            
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.addWidget(remove_btn)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            
            self.sensors_table.setCellWidget(row, 4, btn_widget)
            
    def clear_inputs(self):
        """Clear all input fields."""
        self.sensor_id_input.clear()
        self.port_input.clear()
        self.baudrate_input.setText("9600")
        self.update_config_fields() 