*This is project code for the Udacity [Full-Stack Web Developer Nanodegree](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004)*

# Requirements
- Python 3.6
- Flask 0.12.2

# Installation
## Vagrant Environment
- `$ vagrant up`
- `$ vagrant ssh`
- Go into the `vagrant` directory located in root. You should see `application.py` somewhere in that directory.

## Webserver
- `$ python3 database_setup.py` - This sets up the initial database models
- `$ python3 application.py` - The webserver is now running
- You can browse to `localhost:5000`

# Usage
## API Endpoints
`/api/classroom`
- [GET] will return a list of all classrooms
- [POST] will add new Classroom's
  - `name` - Name of the teacher's Classroom

`/api/classroom/<int:id>`
- [GET] will return information on a specific classroom
- [POST] will create a new Student in classroom with `id`
  - `name` - Name of the Student
  - `description` - A description of the Student
- [DELETE] will delete the Classroom with `id`

`/api/student`
- [GET] will return all Student's in database

`/api/student/<int:id>`
- [GET] will return information on Student with `id`
- [DELETE] will delete Student with `id`
