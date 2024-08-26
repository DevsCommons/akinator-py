from setuptools import setup, find_packages
import datetime

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

current_year = datetime.datetime.now().year

setup(
    name="akinator-py",
    version="0.0.1",
    author="Rio",
    author_email="contact@devrio.org",
    description="A Python library for interacting with the Akinator game API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DevsCommons/akinator-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
        "aiohttp",
        "beautifulsoup4",
    ],
    keywords="akinator game api async",
    project_urls={
        "Bug Reports": "https://github.com/DevsCommons/akinator-py/issues",
        "Source": "https://github.com/DevsCommons/akinator-py",
    },
    license=f"MIT License - Copyright (c) {current_year} Rio",
)
