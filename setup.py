import setuptools

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()
    print(requirements)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="quam_squid_lab",
    version="0.0.1",
    author="SQuID Lab at Niels Bohr Institute, University of Copenhagen",
    author_email="jacob.hastrup@nbi.ku.dk",
    description="QM QuAM components for SQuID Lab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cqed-at-qdev/SQuID-Lab-quam",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    python_requires=">=3.10, <3.12",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
    ],
)
