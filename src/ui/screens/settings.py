import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QPushButton, QFileDialog, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')

class SettingsScreen(QWidget):
    """Settings screen for app configuration."""
    def __init__(self, processor=None):
        super().__init__()
        self.processor = processor
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Connection group
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout(conn_group)
        # Sensor port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Sensor Port:"))
        self.port_edit = QLineEdit()
        port_layout.addWidget(self.port_edit)
        conn_layout.addLayout(port_layout)
        # Sampling rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Sampling Rate (Hz):"))
        self.sampling_rate_spin = QSpinBox()
        self.sampling_rate_spin.setRange(1, 100000)
        self.sampling_rate_spin.setValue(1000)
        rate_layout.addWidget(self.sampling_rate_spin)
        conn_layout.addLayout(rate_layout)
        layout.addWidget(conn_group)

        # Storage group
        storage_group = QGroupBox("Storage")
        storage_layout = QVBoxLayout(storage_group)
        # DB type
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("DB Type:"))
        self.db_combo = QComboBox()
        self.db_combo.addItems(["HDF5", "SQLite", "PostgreSQL"])
        db_layout.addWidget(self.db_combo)
        storage_layout.addLayout(db_layout)
        # HDF5 path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("HDF5 Path:"))
        self.hdf5_path_edit = QLineEdit()
        path_layout.addWidget(self.hdf5_path_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_hdf5)
        path_layout.addWidget(browse_btn)
        storage_layout.addLayout(path_layout)
        # Retention policy
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Retention (days):"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 3650)
        self.retention_spin.setValue(30)
        retention_layout.addWidget(self.retention_spin)
        storage_layout.addLayout(retention_layout)
        layout.addWidget(storage_group)

        # UI Theme group
        theme_group = QGroupBox("UI Theme")
        theme_layout = QHBoxLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)

        # CI/CD group
        cicd_group = QGroupBox("CI/CD")
        cicd_layout = QVBoxLayout(cicd_group)
        # GitHub repo
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("GitHub Repo:"))
        self.repo_edit = QLineEdit()
        repo_layout.addWidget(self.repo_edit)
        cicd_layout.addLayout(repo_layout)
        # Webhook
        webhook_layout = QHBoxLayout()
        webhook_layout.addWidget(QLabel("Webhook URL:"))
        self.webhook_edit = QLineEdit()
        webhook_layout.addWidget(self.webhook_edit)
        cicd_layout.addLayout(webhook_layout)
        # Auto update
        self.auto_update_check = QCheckBox("Enable Auto Update")
        cicd_layout.addWidget(self.auto_update_check)
        layout.addWidget(cicd_group)

        # Save/Load buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        load_btn = QPushButton("Load Settings")
        load_btn.clicked.connect(self.load_settings)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def browse_hdf5(self):
        path, _ = QFileDialog.getSaveFileName(self, "Select HDF5 File", "", "HDF5 Files (*.h5 *.hdf5)")
        if path:
            self.hdf5_path_edit.setText(path)

    def save_settings(self):
        config = {
            "connection": {
                "sensor_port": self.port_edit.text(),
                "sampling_rate": self.sampling_rate_spin.value(),
            },
            "storage": {
                "db_type": self.db_combo.currentText(),
                "hdf5_path": self.hdf5_path_edit.text(),
                "retention_days": self.retention_spin.value(),
            },
            "ui_theme": self.theme_combo.currentText(),
            "cicd": {
                "github_repo": self.repo_edit.text(),
                "webhook_url": self.webhook_edit.text(),
                "auto_update": self.auto_update_check.isChecked(),
            }
        }
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Settings", "Settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def load_settings(self):
        if not os.path.exists(CONFIG_PATH):
            return
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            # Connection
            self.port_edit.setText(config.get("connection", {}).get("sensor_port", ""))
            self.sampling_rate_spin.setValue(config.get("connection", {}).get("sampling_rate", 1000))
            # Storage
            self.db_combo.setCurrentText(config.get("storage", {}).get("db_type", "HDF5"))
            self.hdf5_path_edit.setText(config.get("storage", {}).get("hdf5_path", ""))
            self.retention_spin.setValue(config.get("storage", {}).get("retention_days", 30))
            # UI Theme
            self.theme_combo.setCurrentText(config.get("ui_theme", "Light"))
            # CI/CD
            self.repo_edit.setText(config.get("cicd", {}).get("github_repo", ""))
            self.webhook_edit.setText(config.get("cicd", {}).get("webhook_url", ""))
            self.auto_update_check.setChecked(config.get("cicd", {}).get("auto_update", False))
            QMessageBox.information(self, "Settings", "Settings loaded successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load settings: {str(e)}") 