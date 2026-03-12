from setuptools import setup, find_packages

setup(
    name="file-sentinel",
    version="0.1.0",
    author="Aslam Ahamed",
    description="File integrity monitoring with automatic backup and restore",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/intruderfr/file-sentinel",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Monitoring",
    ],
)
