#!/bin/bash
uvicorn app.main:app --reload
# This script starts the FastAPI application using Uvicorn.
# It runs the app defined in app.main with live reloading enabled.