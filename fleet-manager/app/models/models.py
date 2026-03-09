# /backend/app/models/models.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.core.database import Base

# --- Server Ownership Table ---
class Server(Base):
    __tablename__ = "servers"
    
    # Primary Key - logical server ID
    id = Column(String, primary_key=True) 
    
    # Store the user's ID from the Identity Service (No longer a ForeignKey)
    owner_id = Column(Integer, index=True)
    
    # Store game type and configs to enable redeployment
    game_id = Column(String)
    config = Column(JSON)
    
    # Ephemeral Pod ID, stored to maintain references to active container
    active_pod_name = Column(String, nullable=True)
    
    # Default cost per hour
    hourly_cost = Column(Float, default=0.10) 

# --- Incident Report Table ---
class IncidentReport(Base):
    __tablename__ = "incident_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String, index=True)
    error_line = Column(String)
    recommendation = Column(Text)
    created_at = Column(DateTime, server_default=func.now())