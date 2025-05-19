from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="lab_sensor_app",
    version="0.1.0",
    author="Aitogy",
    author_email="info@aitogy.com",
    description="A real-time sensor data processing platform for lab experiments",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aitogy/lab_sensor_app",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "lab-sensor=lab_sensor_app.cli:main",
        ],
    },
)
