from sqlalchemy.orm import Session
from sql_app.models import Skills
import requests
from sql_app import database
from fastapi import Depends, HTTPException, APIRouter, Header, Body


def seed_skills(db: Session):
    skills_data = [
        {"name": "Python"},
        {"name": "JavaScript"},
        {"name": "React"},
        {"name": "Django"},
        {"name": "Vue.js"},
        {"name": "SQL"},
        {"name": "HTML"},
        {"name": "CSS"},
        {"name": "Flask"},
        {"name": "Angular"},
    ]

    for skill in skills_data:
        db_skill = Skills(**skill)
        db.add(db_skill)

    db.commit()