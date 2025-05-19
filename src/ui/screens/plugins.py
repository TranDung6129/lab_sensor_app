import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QGroupBox, QListWidget, QMessageBox)
from PyQt5.QtCore import Qt

class PluginsScreen(QWidget):
    """Plugin management screen: UI, plugin listing, load/unload, and config display."""
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        self.plugin_dir = "plugins"
        self.setup_ui()
        self.load_available_plugins()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Plugin list
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("""
            QFrame#listFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.addWidget(QLabel("Available Plugins"))
        self.plugin_list = QListWidget()
        list_layout.addWidget(self.plugin_list)

        # Load/Unload buttons
        self.load_btn = QPushButton("Load Plugin")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.load_plugin)
        list_layout.addWidget(self.load_btn)

        self.unload_btn = QPushButton("Unload Plugin")
        self.unload_btn.setEnabled(False)
        self.unload_btn.clicked.connect(self.unload_plugin)
        list_layout.addWidget(self.unload_btn)

        self.plugin_list.currentItemChanged.connect(self.on_plugin_selected)

        # Controls/config panel
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
        self.controls_layout = QVBoxLayout(controls_frame)
        self.controls_layout.setContentsMargins(10, 10, 10, 10)
        self.controls_layout.addWidget(QLabel("Plugin Controls & Configuration"))
        self.config_label = QLabel("Select a plugin to view details.")
        self.controls_layout.addWidget(self.config_label)
        self.controls_layout.addStretch()

        # Add frames to content layout
        content_layout.addWidget(list_frame)
        content_layout.addWidget(controls_frame)
        layout.addLayout(content_layout)

    def load_available_plugins(self):
        """Load list of available plugins from plugin directory."""
        self.plugin_list.clear()
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir)
        plugin_files = [f for f in os.listdir(self.plugin_dir)
                        if f.endswith('.py') and f != '__init__.py']
        for plugin_file in plugin_files:
            plugin_name = os.path.splitext(plugin_file)[0]
            self.plugin_list.addItem(plugin_name)

    def on_plugin_selected(self, current, previous):
        has_selection = current is not None
        self.load_btn.setEnabled(has_selection)
        self.unload_btn.setEnabled(has_selection)
        # Update config panel
        if has_selection:
            plugin_name = current.text()
            plugin_file = plugin_name + ".py"
            self.config_label.setText(f"<b>Plugin:</b> {plugin_name}<br><b>File:</b> {plugin_file}<br><br><i>Configuration options will appear here.</i>")
        else:
            self.config_label.setText("Select a plugin to view details.")

    def load_plugin(self):
        item = self.plugin_list.currentItem()
        if item:
            plugin_name = item.text()
            QMessageBox.information(self, "Load Plugin", f"Plugin '{plugin_name}' loaded (stub).")

    def unload_plugin(self):
        item = self.plugin_list.currentItem()
        if item:
            plugin_name = item.text()
            QMessageBox.information(self, "Unload Plugin", f"Plugin '{plugin_name}' unloaded (stub).") 