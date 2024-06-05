# InfraLCA to LCAx

This repository contains the code to convert the InfraLCA Excel sheet to the LCAx format.
The code is written in Python and uses the LCAx library to convert the data.

The source could be found in the `src` folder and the converted data in the `lcax` folder.

## How to Use

- Install `pipenv`
- Install dependencies and create a new virtual environment by running `pipenv install`
- Run the code by running `pipenv run python src/parse_infralca.py`

The code will read the `src/infralca/InfraLCA_V3.1.xlsm` file and convert it to the LCAx format. 
The converted data will be saved in the `lcax` folder.