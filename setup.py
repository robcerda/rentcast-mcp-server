from setuptools import setup, find_packages

setup(
    name="rentcast-mcp-server",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp[cli]>=1.3.0",
        "httpx>=0.24.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "rentcast-mcp=rentcast_mcp_server.server:main",
        ],
    },
    python_requires=">=3.12",
)