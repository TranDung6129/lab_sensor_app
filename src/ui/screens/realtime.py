from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSlider,
                           QSpinBox, QDoubleSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import logging

logger = logging.getLogger(__name__)

class RealtimeScreen(QWidget):
    """Realtime data visualization screen with time-series plots."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        
        # Initialize UI
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(50)  # Update at 20Hz
        
        logger.info("RealtimeScreen initialized")

    def setup_ui(self):
        """Setup the realtime screen UI layout."""
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
        
        # Time window control
        time_group = QGroupBox("Time Window")
        time_layout = QVBoxLayout(time_group)
        
        time_slider = QSlider(Qt.Horizontal)
        time_slider.setMinimum(1)
        time_slider.setMaximum(60)
        time_slider.setValue(10)
        time_slider.setTickPosition(QSlider.TicksBelow)
        time_slider.setTickInterval(5)
        time_layout.addWidget(time_slider)
        
        time_value = QLabel("10 seconds")
        time_value.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(time_value)
        
        controls_layout.addWidget(time_group)
        
        # Trigger threshold control
        trigger_group = QGroupBox("Trigger Threshold")
        trigger_layout = QVBoxLayout(trigger_group)
        
        threshold_spin = QDoubleSpinBox()
        threshold_spin.setMinimum(0.0)
        threshold_spin.setMaximum(10.0)
        threshold_spin.setValue(2.0)
        threshold_spin.setSingleStep(0.1)
        threshold_spin.setSuffix(" m/s²")
        trigger_layout.addWidget(threshold_spin)
        
        controls_layout.addWidget(trigger_group)
        
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
        
        record_btn = QPushButton("Start Recording")
        record_btn.setCheckable(True)
        record_btn.setStyleSheet("""
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
            QPushButton:checked {
                background-color: #c0392b;
            }
        """)
        layout.addWidget(record_btn)
        
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
                    self.plot_widget.plot(data[channel]['time'],
                                        data[channel]['value'],
                                        name=channel,
                                        pen='b')
                    
                    # Auto-range if needed
                    self.plot_widget.enableAutoRange()
        except Exception as e:
            logger.error(f"Error updating realtime plot: {e}")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        event.accept() 