from pydantic import BaseModel
from typing import Optional, List
from datetime import date



class ProfileCreate(BaseModel):
    profile_type: str
    skills: List[str] = None
    experience: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    profile_image: Optional[str] = None
    user_id: int
    address_area: Optional[str] = None

class ProjectCreate(BaseModel):
    title: str
    description: str
    start_date: date
    end_date: date
    image: str
    skills: List[str]
    profile_id: int

class ProfileUpdate(BaseModel):
    profile_id: int
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address_area: Optional[str] = None 

class ExperienceCreate(BaseModel):
    title: str
    profile_id: int
    company: str
    location: Optional[str]
    start_date: date
    end_date: Optional[date]
    description: Optional[str]

class EducationCreate(BaseModel):
    user_id: int
    institution_name: str
    degree: str
    start_year: int
    end_year: Optional[int]
