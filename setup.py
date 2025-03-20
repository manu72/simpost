from setuptools import setup, find_packages

setup(
    name="simpost",
    version="0.1.0",
    description="A tool for automating multi-feed news processing",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "requests",
        "feedparser",
    ],
    python_requires=">=3.8",
) 