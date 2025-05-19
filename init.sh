#!/bin/bash

# Create necessary directories
mkdir -p src/core
mkdir -p src/acquisition
mkdir -p src/preprocessing
mkdir -p src/integration
mkdir -p src/estimation
mkdir -p src/visualization
mkdir -p src/anomaly
mkdir -p src/storage
mkdir -p src/plugin
mkdir -p src/utils
mkdir -p tests
mkdir -p docs
mkdir -p examples
mkdir -p .github/workflows

# Create __init__.py files
touch src/__init__.py
touch src/core/__init__.py
touch src/acquisition/__init__.py
touch src/preprocessing/__init__.py
touch src/integration/__init__.py
touch src/estimation/__init__.py
touch src/visualization/__init__.py
touch src/anomaly/__init__.py
touch src/storage/__init__.py
touch src/plugin/__init__.py
touch src/utils/__init__.py

# Create test files
touch tests/__init__.py
touch tests/test_interfaces.py
touch tests/test_acquisition.py
touch tests/test_preprocessing.py
touch tests/test_integration.py
touch tests/test_estimation.py
touch tests/test_visualization.py
touch tests/test_anomaly.py
touch tests/test_storage.py
touch tests/test_plugin.py

# Create documentation files
touch docs/SRS.md
touch docs/HLD.md
touch docs/user_guide.md

# Create example file
touch examples/live_demo.py

# Initialize git if not already initialized
if [ ! -d .git ]; then
    git init
    git add .
    git commit -m "Initial commit"
fi

# Make init.sh executable
chmod +x init.sh

echo "Project structure initialized successfully!"
