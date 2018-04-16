#Requirements
- Python 3.6
- Flask 0.12.2


# Installation
## Vagrant Environment
`$ vagrant up`
`$ vagrant ssh`
Go into the `vagrant` directory located in root. You should see `application.py` somewhere in that directory.

## Webserver
`$ python3 database_setup.py` - This sets up the initial database models
`$ python3 application.py`
The webserver is now running. You can browse to `localhost:5000`

# Usage
## API Endpoints
`/api/classroom`
- GET will return a list of all classrooms
- POST will add new classrooms
-- `name` - Name of the teacher's classroom
