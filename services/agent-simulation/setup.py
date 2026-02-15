"""
Setup script for Agent Simulation Engine SDK.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-simulation-engine",
    version="0.1.0",
    author="Lyzr",
    author_email="support@lyzr.ai",
    description="Official Python SDK for the Lyzr Agent Simulation Engine (A-Sim) platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LyzrCore/agent-simulation-engine",
    project_urls={
        "Bug Tracker": "https://github.com/LyzrCore/agent-simulation-engine/issues",
        "Documentation": "https://docs.lyzr.ai/agent-simulation-engine",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.28.0",
        ],
    },
    keywords=[
        "lyzr",
        "agent",
        "simulation",
        "testing",
        "ai",
        "llm",
        "evaluation",
        "sdk",
    ],
)
