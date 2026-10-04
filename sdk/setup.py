from setuptools import setup, find_packages

setup(
    name="agentmemory",
    version="0.1.0",
    description="Python SDK for Agent Memory OS — persistent memory for AI agents",
    packages=find_packages(),
    install_requires=["httpx>=0.27.0"],
    python_requires=">=3.9",
)
