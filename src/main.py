import sys
import logging
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow(processor=None)  # Pass None as processor for now
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 