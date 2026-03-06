# /app/models/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class IncidentReport(Base):
    __tablename__ = "incident_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, index=True)
    error_line = Column(String)
    recommendation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())