# /usr/bin/env python3

import sys
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()


class Classroom(Base):
    __tablename__ = 'classroom'
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Student(Base):
    __tablename__ = 'student'
    name = Column(String(80), nullable=False)
    description = Column(String(500))
    classroom_id = Column(Integer, ForeignKey('classroom.id'))
    created_date = Column(DateTime, default=datetime.datetime.utcnow)
    id = Column(Integer, primary_key=True)
    classroom = relationship(Classroom)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_date': self.created_date,
            'classroom_id': self.classroom_id
        }


engine = create_engine('sqlite:///classroomdb.db')
Base.metadata.create_all(engine)
