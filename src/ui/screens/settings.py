import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QGroupBox, QPushButton, QFileDialog, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt

# Giả sử CONFIG_PATH được định nghĩa ở đâu đó trong ứng dụng của bạn, ví dụ:
# utils/config_manager.py hoặc tương tự để quản lý đường dẫn tập tin cấu hình
# Để ví dụ này chạy độc lập, chúng ta sẽ định nghĩa nó ở đây.
# Trong ứng dụng thực tế, bạn nên quản lý nó một cách tập trung.
APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
CONFIG_PATH = os.path.join(APP_ROOT, 'src', 'config.json')


class SettingsScreen(QWidget):
    """Settings screen for general application configuration."""
    def __init__(self, processor=None): # processor có thể không cần thiết nữa nếu không có setting nào liên quan trực tiếp
        super().__init__()
        # self.processor = processor # Xem xét lại sự cần thiết của processor
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Storage group
        storage_group = QGroupBox("Cấu hình Lưu trữ (Storage)")
        storage_layout = QVBoxLayout(storage_group)
        
        # DB type
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Loại Cơ sở dữ liệu (DB Type):"))
        self.db_combo = QComboBox()
        self.db_combo.addItems(["HDF5", "SQLite", "PostgreSQL"])
        db_layout.addWidget(self.db_combo)
        storage_layout.addLayout(db_layout)
        
        # HDF5 path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Đường dẫn HDF5 (HDF5 Path):"))
        self.hdf5_path_edit = QLineEdit()
        path_layout.addWidget(self.hdf5_path_edit)
        browse_btn = QPushButton("Duyệt...")
        browse_btn.clicked.connect(self.browse_hdf5)
        path_layout.addWidget(browse_btn)
        storage_layout.addLayout(path_layout)
        
        # Retention policy
        retention_layout = QHBoxLayout()
        retention_layout.addWidget(QLabel("Thời gian lưu trữ (ngày):"))
        self.retention_spin = QSpinBox()
        self.retention_spin.setRange(1, 3650) # Ví dụ: lên đến 10 năm
        self.retention_spin.setValue(30)
        retention_layout.addWidget(self.retention_spin)
        storage_layout.addLayout(retention_layout)
        layout.addWidget(storage_group)

        # UI Theme group
        theme_group = QGroupBox("Giao diện Người dùng (UI Theme)")
        theme_layout = QHBoxLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"]) # Có thể thêm các theme khác
        theme_layout.addWidget(QLabel("Chủ đề (Theme):"))
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)

        # CI/CD group
        cicd_group = QGroupBox("Tích hợp & Triển khai Liên tục (CI/CD)")
        cicd_layout = QVBoxLayout(cicd_group)
        
        # GitHub repo
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(QLabel("Kho GitHub (GitHub Repo):"))
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
        self.auto_update_check = QCheckBox("Kích hoạt Tự động cập nhật (Enable Auto Update)")
        cicd_layout.addWidget(self.auto_update_check)
        layout.addWidget(cicd_group)

        # Save/Load buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch() # Đẩy các nút về bên phải
        save_btn = QPushButton("Lưu Cài đặt")
        save_btn.setStyleSheet("padding: 8px 15px; font-size: 14px;")
        save_btn.clicked.connect(self.save_settings)
        
        load_btn = QPushButton("Tải lại Cài đặt")
        load_btn.setStyleSheet("padding: 8px 15px; font-size: 14px;")
        load_btn.clicked.connect(self.load_settings_confirmation) # Thêm xác nhận trước khi tải lại
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def browse_hdf5(self):
        path, _ = QFileDialog.getSaveFileName(self, "Chọn hoặc Tạo tệp HDF5", "", "HDF5 Files (*.h5 *.hdf5)")
        if path:
            self.hdf5_path_edit.setText(path)

    def save_settings(self):
        # Đảm bảo thư mục cho CONFIG_PATH tồn tại
        config_dir = os.path.dirname(CONFIG_PATH)
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir)
            except OSError as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể tạo thư mục cấu hình: {str(e)}")
                return

        config = {
            # Loại bỏ "connection" settings khỏi đây
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
                json.dump(config, f, indent=4) # Sử dụng indent=4 cho dễ đọc
            QMessageBox.information(self, "Cài đặt", "Cài đặt đã được lưu thành công.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu cài đặt: {str(e)}")

    def load_settings_confirmation(self):
        reply = QMessageBox.question(self, 'Xác nhận', 
                                     "Bạn có chắc chắn muốn tải lại cài đặt không? Các thay đổi chưa lưu sẽ bị mất.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.load_settings()

    def load_settings(self):
        if not os.path.exists(CONFIG_PATH):
            QMessageBox.information(self, "Cài đặt", "Không tìm thấy tệp cấu hình. Sử dụng cài đặt mặc định.")
            # Thiết lập giá trị mặc định nếu cần
            self.db_combo.setCurrentText("HDF5")
            self.hdf5_path_edit.setText("")
            self.retention_spin.setValue(30)
            self.theme_combo.setCurrentText("Light")
            self.repo_edit.setText("")
            self.webhook_edit.setText("")
            self.auto_update_check.setChecked(False)
            return
            
        try:
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
            
            # Storage
            storage_config = config.get("storage", {})
            self.db_combo.setCurrentText(storage_config.get("db_type", "HDF5"))
            self.hdf5_path_edit.setText(storage_config.get("hdf5_path", ""))
            self.retention_spin.setValue(storage_config.get("retention_days", 30))
            
            # UI Theme
            self.theme_combo.setCurrentText(config.get("ui_theme", "Light"))
            
            # CI/CD
            cicd_config = config.get("cicd", {})
            self.repo_edit.setText(cicd_config.get("github_repo", ""))
            self.webhook_edit.setText(cicd_config.get("webhook_url", ""))
            self.auto_update_check.setChecked(cicd_config.get("auto_update", False))
            
            # Không cần thông báo thành công ở đây nữa nếu không có tệp
            # QMessageBox.information(self, "Cài đặt", "Cài đặt đã được tải thành công.")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể tải cài đặt: {str(e)}")
            # Có thể reset về mặc định ở đây nếu tải lỗi