#!/usr/bin/env python3
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.ussd.ussd_routers import router as registration_router
from routes.consultation.consultation import router as consultation_router
from routes.auth.auth_router import router as auth_router
from routes.history.history_router import router as history_router
from routes.notifications.notifications_router import router as notifications_router
from database.session import get_db

app = FastAPI(title="MedCall APIs",
              description="Telemedecine/Telehealth app using USSD and SMS",
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(registration_router)
app.include_router(consultation_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(notifications_router)

@app.get("/")
async def root():
    return {"message": "Welcome to MedCall"}

@app.get("/health")
async def health_check():
    return {"health_check":"successful"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
