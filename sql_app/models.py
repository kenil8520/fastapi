from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, Table, Date
from sql_app.database import Base
from sqlalchemy.orm import relationship


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, index=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    social_type = Column(String)
    access_token = Column(String)
    password = Column(String)
    is_verified = Column(Boolean)
    verification_code = Column(Integer)
    
    profiles = relationship("Profile", back_populates="user")
    educations = relationship("Education", back_populates="user")  # New relationship

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    profile_type = Column(String, index=True)
    experience = Column(Integer)
    email = Column(String)
    phone_country = Column(String)
    phone = Column(String)
    profile_image = Column(String)
    full_name = Column(String)
    address_area = Column(String)
    link = Column(String)
    github = Column(String)
    bitbucket = Column(String)
    gitlab = Column(String)
    
    user = relationship("User", back_populates="profiles")
    job_experiences = relationship("Experience", back_populates="profile")
    projects = relationship("Project", back_populates="profile")
    skills = relationship("Skills", secondary="profile_skills", back_populates="profiles")
    certificates = relationship("Certificate", back_populates="profile")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    title = Column(String, index=True)
    description = Column(String)
    start_date = Column(Date)  
    end_date = Column(Date)  
    image = Column(String)
    
    profile = relationship("Profile", back_populates="projects")
    skills = relationship("Skills", secondary="project_skills", back_populates="projects")

class Skills(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    profiles = relationship("Profile", secondary="profile_skills", back_populates="skills")
    projects = relationship("Project", secondary="project_skills", back_populates="skills")

class ProfileSkills(Base):
    __tablename__ = "profile_skills"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))
    
class ProjectSkills(Base):
    __tablename__ = "project_skills"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))

class Experience(Base):
    __tablename__ = "job_experiences"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    title = Column(String, index=True)
    company = Column(String)
    location = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    description = Column(String)
    
    profile = relationship("Profile", back_populates="job_experiences")


class Education(Base):
    __tablename__ = "educations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    degree = Column(String)
    start_year = Column(Integer)
    end_year = Column(Integer)

    user = relationship("User", back_populates="educations")
    institution = relationship("Institution")


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    description = Column(String)
    # Add other fields as needed

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"))
    name = Column(String)
    issuer = Column(String)
    issue_date = Column(Date)
    expiration_date = Column(Date)

    profile = relationship("Profile", back_populates="certificates")
