from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="latta-python-recorder",
    version="0.0.3",
    description="Latta AI Vanilla Python Recorder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Latta AI s.r.o.",
    author_email="info@latta.ai",
    url="https://latta.ai",
    packages=find_packages(),
    install_requires=[
        "psutil",       # Required for system info
        "requests",     # Required for HTTP requests
    ],
    python_requires=">=3.8",
)
