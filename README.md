# euro2022
This is the prototype of a dashboard that can be used to analyse the different teams.
It uses free statsbomb event- and 360-data of the women euro 2022.
## get it running
First you need to clone this repo:
`git clone `
Afterwards you can install the nesseccary packages in a virtual enviroment.
The enviroment you can create by (on mac):
`python -m venv venv`
and activate it by:
`source venv/bin/activate`
Now the package can be installed by (using python 3.11.1):
`poetry install`
You host the dashboard locally by executing:
`poetry run streamlit run streamlit_app.py`
