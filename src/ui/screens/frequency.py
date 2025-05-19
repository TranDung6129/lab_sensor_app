from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QComboBox, QSpinBox,
                           QDoubleSpinBox, QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FrequencyScreen(QWidget):
    """Frequency analysis screen with FFT plots and controls."""
    
    def __init__(self, processor):
        super().__init__()
        self.processor = processor
        
        # Initialize UI
        self.setup_ui()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(100)  # Update at 10Hz
        
        logger.info("FrequencyScreen initialized")

    def setup_ui(self):
        """Setup the frequency analysis screen UI layout."""
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
        self.plot_widget.setLabel('left', 'Magnitude')
        self.plot_widget.setLabel('bottom', 'Frequency', 'Hz')
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
        
        # FFT settings
        fft_group = QGroupBox("FFT Settings")
        fft_layout = QVBoxLayout(fft_group)
        
        # Window size
        window_layout = QHBoxLayout()
        window_label = QLabel("Window Size:")
        window_layout.addWidget(window_label)
        
        self.window_size = QSpinBox()
        self.window_size.setMinimum(256)
        self.window_size.setMaximum(8192)
        self.window_size.setValue(1024)
        self.window_size.setSingleStep(256)
        window_layout.addWidget(self.window_size)
        fft_layout.addLayout(window_layout)
        
        # Window type
        window_type_layout = QHBoxLayout()
        window_type_label = QLabel("Window Type:")
        window_type_layout.addWidget(window_type_label)
        
        self.window_type = QComboBox()
        self.window_type.addItems(["Hanning", "Hamming", "Blackman", "Rectangular"])
        window_type_layout.addWidget(self.window_type)
        fft_layout.addLayout(window_type_layout)
        
        # Overlap
        overlap_layout = QHBoxLayout()
        overlap_label = QLabel("Overlap:")
        overlap_layout.addWidget(overlap_label)
        
        self.overlap = QSpinBox()
        self.overlap.setMinimum(0)
        self.overlap.setMaximum(90)
        self.overlap.setValue(50)
        self.overlap.setSuffix("%")
        overlap_layout.addWidget(self.overlap)
        fft_layout.addLayout(overlap_layout)
        
        controls_layout.addWidget(fft_group)
        
        # Display options
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        
        self.log_scale = QCheckBox("Logarithmic Scale")
        self.log_scale.setChecked(True)
        display_layout.addWidget(self.log_scale)
        
        self.show_peaks = QCheckBox("Show Peak Frequencies")
        self.show_peaks.setChecked(True)
        display_layout.addWidget(self.show_peaks)
        
        controls_layout.addWidget(display_group)
        
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
        
        export_btn = QPushButton("Export FFT")
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
        layout.addWidget(export_btn)
        
        return toolbar

    def update_data(self):
        """Update the FFT plot with latest data."""
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
                    # Get FFT parameters
                    window_size = self.window_size.value()
                    window_type = self.window_type.currentText().lower()
                    overlap = self.overlap.value() / 100.0
                    
                    # Calculate FFT
                    signal = data[channel]['value']
                    if len(signal) >= window_size:
                        # Apply window
                        if window_type == 'hanning':
                            window = np.hanning(window_size)
                        elif window_type == 'hamming':
                            window = np.hamming(window_size)
                        elif window_type == 'blackman':
                            window = np.blackman(window_size)
                        else:  # rectangular
                            window = np.ones(window_size)
                            
                        # Calculate FFT
                        fft = np.fft.rfft(signal[-window_size:] * window)
                        freqs = np.fft.rfftfreq(window_size, d=1.0/self.processor.sample_rate)
                        
                        # Convert to magnitude spectrum
                        magnitude = np.abs(fft)
                        if self.log_scale.isChecked():
                            magnitude = 20 * np.log10(magnitude + 1e-10)
                            
                        # Update plot
                        self.plot_widget.clear()
                        self.plot_widget.plot(freqs, magnitude, name=channel, pen='b')
                        
                        # Show peaks if enabled
                        if self.show_peaks.isChecked():
                            from scipy.signal import find_peaks
                            peaks, _ = find_peaks(magnitude, height=np.max(magnitude)*0.1)
                            for peak in peaks:
                                self.plot_widget.plot([freqs[peak]], [magnitude[peak]], 
                                                    pen=None, symbol='o', symbolSize=10,
                                                    symbolBrush='r')
                        
                        # Auto-range if needed
                        self.plot_widget.enableAutoRange()
        except Exception as e:
            logger.error(f"Error updating FFT plot: {e}")

    def closeEvent(self, event):
        """Handle widget close event."""
        self.update_timer.stop()
        event.accept() 