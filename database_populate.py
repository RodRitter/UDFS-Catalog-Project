# /usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Classroom, Student

engine = create_engine("sqlite:///classroomdb.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Dummy data to populate database with. (CATEGORY:[ARRAY_OF_ITEMS])
dummy_data = {
    "Mrs Smith": ["John", "Keegan", "Mason", "Kinley", "Reyna", "Danika"],
    "Mr Langley": ["Alonzo", "Immanuel", "Matthew", "Brooklynn", "Penelope", "Addison"],
    "Mrs Exelby": ["Grady", "Christian", "Braiden", "Brenna", "Tess", "Megan"],
    "Mr Deppe": ["Bryce", "Camren", "Philip", "Kyra", "Serena", "Rose"]
}

# Parse dummy_data - Create Category & Item combinations
for classroom_name in dummy_data:
    cat = Classroom(name = classroom_name)
    session.add(cat)
    for student_name in dummy_data[classroom_name]:
        query = session.query(Student).filter_by(name = student_name).first()
        if query == None:
            item = Student(name = student_name, description = "No Description", classroom = cat)
            session.add(item)
            print("Added Item: {}".format(student_name))
        else:
            print("{} already exists. Skipping.".format(student_name))
        

session.commit()
