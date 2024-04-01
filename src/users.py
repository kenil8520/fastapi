# users.py

from fastapi import Depends, HTTPException, APIRouter, Header, Body, Path, File, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sql_app import database
from sql_app.models import Profile, User, Country, Project, Experience, ProfileSkills, Skills, ProjectSkills, Institution, Education
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
# import PyPDF2
import random
import requests
from typing import List, Dict
from sql_app.schemas import ProfileCreate, ProjectCreate, ProfileUpdate, ExperienceCreate, EducationCreate
# import fitz
import re
from fastapi.responses import JSONResponse




# GOOGLE_CLIENT_ID = "your_google_client_id"



router = APIRouter()


# Secret key to sign JWT tokens (replace this with a secure random key in production)
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing
password_hashing = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="Authorization")


# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        print(email)
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user

# Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to generate a random verification code
def generate_verification_code():
    return str(random.randint(100000, 999999))


@router.get("/")
def home():
    return {"message": "API working"}


@router.post("/register", tags=["auth"])
def register_user(email: str = Body(...), password: str = Body(...), name: str = Body(...), db: Session = Depends(get_db)):
    # Check if the username already exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="User already registered")

    # Hash the password (you should use a proper password hashing library)
    hashed_password = password_hashing.hash(password)

    # Generate a random verification code (for demonstration purposes)
    # verification_code = generate_verification_code()
    verification_code = 111111

    # Create a new user in the database
    new_user = User(email=email, password=hashed_password, name=name, verification_code=verification_code)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully, Please check your mail for Verification", "status": True}

@router.post("/login", tags=["auth"])
def login_user(email: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.email == email).first()
    if not user or not password_hashing.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    profiles = db.query(Profile).filter(Profile.user_id == user.id).all()

    # Generate JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "name": user.name,
            "profiles": profiles
        }, 
        "status": True, 
        "message": "User login successfully"
    }


@router.post("/verify-email", tags=["auth"])
def verify_email(email: str = Body(...), verification_code: str = Body(...), db: Session = Depends(get_db)):
    # Retrieve the user by email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the verification code matches
    if str(user.verification_code) != verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Mark the user as verified 
    user.is_verified = True
    db.commit()

    # Generate JWT token for the verified user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "user": user, "status": True, "message": "Email verified successfully"}


# Endpoint to validate Google Sign-In token
@router.post("/validate-google-token", tags=["auth"])
def validate_google_token(access_token: str = Body(...), email: str = Body(...), db: Session = Depends(get_db)):
    headers = {"Authorization": f"Bearer {access_token}"}
    google_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers=headers,
    )
    google_data = google_response.json()

    print(google_data, access_token)
    if "error" in google_data:
        raise HTTPException(status_code=401, detail="Invalid Google Sign-In")

    email = google_data.get("email")
     # Check if the user already exists in the database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create a new user in the database
        new_user = User(email=email, name=google_data.get("name", ""), is_verified=True, social_type='GOOGLE')  
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        user = new_user

    # Generate JWT token for the verified user
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    return {"message": "User login successfully", "access_token": access_token, "user": user, "status": True}


@router.post("/create_profile/", tags=["profile"])
def create_profile(profile_data: ProfileCreate, db: Session = Depends(get_db)):
    user_id = profile_data.user_id  # Adjust this based on your authentication mechanism
    skills_data = profile_data.skills  # Remove skills from the profile data

    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Create a new profile
    new_profile = Profile(**profile_data.dict(exclude={'skills'}))
    db.add(new_profile)
    db.commit()

    for skill in skills_data:
        skill_db = db.query(Skills).filter(Skills.name == skill).first()
        if not skill_db:
            skill_db = Skills(**skill.dict())
            db.add(skill_db)
            db.commit()

        profile_skill = ProfileSkills(profile_id=new_profile.id, skill_id=skill_db.id)
        db.add(profile_skill)

    db.commit()
    db.refresh(new_profile)
    new_profile.skills = profile_skill
    return { "data": new_profile, "status": True, "message": "Profile created successfully"}

@router.put("/update_profile", tags=["profile"])
def update_profile(
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    # Get the user's profile
    user_profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Update profile fields
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(user_profile, field, value)

    # Commit changes to the database
    db.commit()
    db.refresh(user_profile)
    return { "data": user_profile, "status": True, "message": "User profile updated successfully"} 

@router.get("/user_profiles/{user_id}", tags=["profile"])
def get_user_profiles(user_id: int, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profiles = db.query(Profile).filter(Profile.user_id == user_id).all()
    return { "data": profiles, "status": True, "message": "Profiles fetched successfully"} 

@router.get("/profile/{profile_id}", tags=["profile"])
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    # Get the profile by ID
    profile = db.query(Profile).options(joinedload(Profile.projects).joinedload(Project.skills), joinedload(Profile.job_experiences)).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return { "data": profile, "status": True, "message": "Profile fetched successfully"} 


@router.post("/add_project", tags=["project"])
def add_project(
    project_create: ProjectCreate,
    db: Session = Depends(get_db)
):
    # Check if the user has a profile
    profile_id = project_create.profile_id
    skills_data = project_create.skills  # Remove skills from the profile data

    # Check if the profile exists
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create a new project
    new_project = Project(**project_create.dict(exclude={'skills'}))
    # Add the new project to the database
    db.add(new_project)
    db.commit()
    # db.refresh(new_project)

    for skill in skills_data:
        skill_db = db.query(Skills).filter(Skills.name == skill).first()
        if not skill_db:
            skill_db = Skills(name=skill)
            db.add(skill_db)
            db.commit()

        project_skill = ProjectSkills(project_id=new_project.id, skill_id=skill_db.id)
        db.add(project_skill)

    db.commit()
    db.refresh(new_project)
    return { "data": new_project, "status": True, "message": "Project created successfully"} 

@router.get("/projects/{project_id}", tags=["project"])
def get_project_details(
    project_id: int = Path(..., title="The ID of the project to get details", gt=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert the project data to a Pydantic model
    project_details = ProjectDetail(**project.__dict__)

    return project_details

@router.get("/projects", tags=["project"])
def get_projects(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if the current user has access to the specified profile
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Retrieve the list of projects for the specified profile
    projects = db.query(Project).filter(Project.profile_id == profile_id).all()
    return {"data": projects, "status": True, "message": "Projects retrieved successfully for profile_id: {}".format(profile_id)}


    # current_user: User = Depends(get_current_user),

@router.post("/add_experience")
def add_experience(
    experience_create: ExperienceCreate,
    db: Session = Depends(get_db)
):
    # Check if the user has a profile
    user_profile = db.query(Profile).filter(Profile.id == experience_create.profile_id).first()
    if not user_profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    # Create a new experience
    new_experience = Experience(**experience_create.dict())

    # Add the new experience to the database
    db.add(new_experience)
    db.commit()
    db.refresh(new_experience)
    return new_experience

@router.get("/experiences/{profile_id}")
def get_experiences(profile_id: int, db: Session = Depends(get_db)):
    # Check if the profile exists
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Get the experiences for the given profile ID
    experiences = db.query(Experience).filter(Experience.profile_id == profile_id).all()
    return { "data": experiences, "status": True, "message": "experiance data fetched successfully"} 


@router.post("/add_education")
def add_education(education_create: EducationCreate, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == education_create.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the institution exists or create a new one
    institution = db.query(Institution).filter(Institution.name == education_create.institution_name).first()
    if not institution:
        institution = Institution(name=education_create.institution_name)
        db.add(institution)
        db.commit()
        db.refresh(institution)

    # Create a new education record
    new_education = Education(
        user_id=education_create.user_id,
        institution_id=institution.id,
        degree=education_create.degree,
        start_year=education_create.start_year,
        end_year=education_create.end_year,
    )

    # Add the new education record to the database
    db.add(new_education)
    db.commit()
    db.refresh(new_education)
    return {"data": new_education, "status": True, "message": "Education details added  successfully"}

@router.get("/get_educations/{user_id}")
def get_educations(user_id: int, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve the list of education details with joined institution data
    educations = (
        db.query(Education)
        .join(Institution)
        .options(joinedload(Education.institution))
        .filter(Education.user_id == user_id)
        .all()
    )

    # Map the results to the response model
    # education_response_list = [
    #     EducationResponse(
    #         id=edu.id,
    #         user_id=edu.user_id,
    #         institution_name=edu.institution.name,
    #         degree=edu.degree,
    #         start_year=edu.start_year,
    #         end_year=edu.end_year,
    #     )
    #     for edu in educations
    # ]
    return {"data": educations, "status": True, "message": "Education data fetched  successfully"}

@router.get("/countries/")
def get_countries(db: Session = Depends(get_db)):
    countries = db.query(Country).all()
    return { "data": countries, "status": True, "message": "Countries fetched successfully"} 



