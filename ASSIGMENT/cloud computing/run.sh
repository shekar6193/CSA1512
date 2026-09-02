#!/usr/bin/env bash
set -e

echo "========================================================================="
echo "   CampusPulse Cloud - Smart Campus Service Request & Incident Response"
echo "========================================================================="
echo ""

python3 -m pip install -r requirements.txt email-validator
echo ""
echo "Starting application on http://localhost:8000 ..."
echo "OpenAPI Swagger documentation: http://localhost:8000/docs"
echo ""
python3 main.py
