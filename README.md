# MAPBackend
The Backend for CS307 Project

## Python --version
* Python 3.10.6

## Steps to getting this setup
* clone this repo (creates a local copy of the repo)
* cd MAPBackend 
* virtualenv venv (creates a virtualenvironment named venv)
* source venv/bin/activate (activates the virtualenvironment any package you install inside it will be local to the project)
* pip install -r requirements.txt (downloads all the packages needed for the project)

* deactivate (ATTENTION: use only if you want to deactivate the virtualenv, probably before closing the project)

## To run the app
* uvicorn main:app --reload



