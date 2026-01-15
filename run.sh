#!/bin/bash

# AI Voice Conversation System Startup Script

# Activate conda environment
echo "Activating conda environment: talk_demo_env"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate talk_demo_env

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r backend/requirements.txt -q

# Start the backend server
echo "Starting backend server on http://localhost:8000"
echo "Frontend available at http://localhost:8000 (served by FastAPI)"
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
