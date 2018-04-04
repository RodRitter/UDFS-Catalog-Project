# /usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item

engine = create_engine("sqlite:///itemcatalogue.db")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Dummy data to populate database with. (CATEGORY:[ARRAY_OF_ITEMS])
dummy_data = {
    "Soccer": ["Soccer Ball", "Goalie Gloves", "Soccer Boots"],
    "Rugby": ["Rugby Ball", "Mouth Guard", "Rugby Boots"],
    "Cricket": ["Cricket Bat", "Cricket Ball", "Cricket Cap"]
}

# Parse dummy_data - Create Category & Item combinations
for cat_name in dummy_data:
    cat = Category(name = cat_name)
    session.add(cat)
    for item_name in dummy_data[cat_name]:
        item = Item(name = item_name, description = "This is a {}".format(item_name), category = cat)
        session.add(item)

session.commit()
