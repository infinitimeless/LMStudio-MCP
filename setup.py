from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lmstudio-mcp",
    version="0.1.0",
    author="infinitimeless",
    author_email="127632852+infinitimeless@users.noreply.github.com",
    description="A Model Control Protocol (MCP) server that allows Claude to communicate with locally running LLM models via LM Studio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/infinitimeless/LMStudio-MCP",
    packages=find_packages(),
    py_modules=["lmstudio_bridge"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests",
        "mcp[cli]>=1.2,<2",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lmstudio-mcp=lmstudio_bridge:main",
        ],
    },
)