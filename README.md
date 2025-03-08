# NO2 Pollution Prediction for Tokyo

This repository contains the backend and frontend components for a project that predicts NO₂ pollution levels in Tokyo.

## Project Overview
The system leverages machine learning techniques to analyze and predict nitrogen dioxide (NO₂) pollution based on historical and real-time data. It is designed as a full-stack application with both backend and frontend components.

## Features
- Predicts NO₂ pollution levels for Tokyo
- Full-stack application with a dedicated backend and frontend
- Dockerized for easy deployment (not available yet)

## Installation & Setup (not available yet)
Ensure you have [Docker](https://www.docker.com/) installed on your machine. To run the project, simply execute:

```sh
docker compose up -d
```

This will start both the backend and frontend services in detached mode.

### Running Without Docker
If you prefer to run the project without Docker, follow these steps:

#### Backend Setup
1. Navigate to the backend directory:
   ```sh
   cd backend
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Start the backend server:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup
1. Navigate to the frontend directory:
   ```sh
   cd frontend
   ```
2. Install dependencies (requires Node.js and npm):
   ```sh
   npm install
   ```
3. Start the frontend server:
   ```sh
   npm run dev
   ```

## Usage
Once the services are up and running, access the application via the provided frontend URL. The system will process the necessary data and display NO₂ pollution predictions.

## Technologies Used
- **Backend:** Python, FastAPI
- **Frontend:** Next.JS
- **Docker:** For containerized deployment (not available)

## Contributing
Feel free to fork this repository and submit pull requests with improvements or bug fixes.

