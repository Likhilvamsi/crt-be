from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.db import models
from src.db.database import engine
from src.api import auth_router, app_admin_router, college_admin_router, branch_admin_router, student_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="College Management System")

# CORS settings
origins = [
    "http://localhost:3000",   # React/Next.js
    "http://127.0.0.1:3000",
    "*",  # allow all (not recommended for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(app_admin_router.router)
app.include_router(college_admin_router.router)
app.include_router(branch_admin_router.router)
app.include_router(student_router.router)
