# gbtgridder

A stand-alone spectral gridder and imager for the Green Bank Telescope

## Installation

```bash
# Will currently only work within the GBO network, after configuring to use the private PyPI repo
pip install gbtgridder
```

## Development

In order to set up your development environment:

`gbtgridder` current requires `python>=3.6,<3.9`.

```bash
git clone https://github.com/GreenBankObservatory/gbtgridder
cd gbtgridder
# Create venv somewhere, doesn't have to be here
python -m venv .venv
source .venv/bin/activate
# Not required, but recommended
pip install -U pip setuptools wheel build
pip install -r requirements-dev.txt
pip install -e .
pre-commit install
```
