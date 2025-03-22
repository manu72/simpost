from setuptools import setup, find_packages

setup(
    name="simpost",
    version="0.1.0",
    description="A tool for automating multi-feed news processing",
    author="Manu Hume",
    author_email="manu@throwingeights.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "requests",
        "feedparser",
        "openai",
    ],
    python_requires=">=3.8",
) 