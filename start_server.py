import os
import subprocess
import sys

# Define the project directory and data folder
project_directory = os.path.dirname(os.path.abspath(__file__))
data_directory = os.path.join(project_directory, 'data')

# Create the data directory if it does not exist
if not os.path.exists(data_directory):
    os.makedirs(data_directory)
    print(f"Created directory: {data_directory}")

# Check if Flask and Flask-CORS are installed
try:
    import flask
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("Flask or Flask-CORS not found. Installing required packages...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-cors'])

# Verify that server.py exists before starting it
server_file = os.path.join(project_directory, 'server.py')

if os.path.exists(server_file):
    # Run the server file using subprocess
    print(f"Starting the existing Flask server: {server_file}")
    subprocess.run([sys.executable, 'server.py'])
else:
    print(f"server.py not found in {project_directory}. Please ensure it exists.")
