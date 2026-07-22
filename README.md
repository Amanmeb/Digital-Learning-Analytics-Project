#Setting the project

# CDLAID Learning Analytics API

## Requirements

- Python 3.12+
- PostgreSQL
- Docker (for production deployment)

The project requires Python 3.12 because FastAPI 0.138.2 and the dependency stack are pinned for Python 3.12.

## Local Development Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Digital-Learning-Analytics-Project```

### 2 Create virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate

### 3

For windows:
.venv\Scripts\activate

### 4 Installl dependencies
pip install -r backend/requirements.txt

### 5 Create a .env file in the project root 
DATABASE_URL=postgresql://username:password@localhost:5432/cdlaid_analytics
API_SECRET_KEY=your_secret_key
ENVIRONMENT=development

### 6. Start the API

The backend uses the `backend/app` package structure.

Run:

```bash
PYTHONPATH=$(pwd)/backend uvicorn api.main:app --reload

### 7 Swagger documentation
Open:
http://127.0.0.1:8000/api/docs


# Camara Digital Learning Analytics and Impact Dashboard

CDLAID is a centralised digital learning analytics platform built for
Camara Education Ethiopia. It collects learning activity data from
school servers, transforms it into structured analytics, and presents
insights through interactive dashboards.

## System Overview

- School servers run Moodle as the local learning platform
- Learning events are captured as xAPI statements
- Events are queued locally and synced to the central server
- PostgreSQL stores and structures all data
- dbt transforms raw data into dashboard-ready tables
- Apache Superset serves all dashboards to users via browser

## Repository Structure

api/                FastAPI ingestion API and admin panel
edge/               SQLite queue and sync agent for school servers
dbt/                dbt transformation models
sql/                PostgreSQL schema migrations
scripts/            Installation and deployment scripts
superset/           Dashboard configurations
moodle/             Moodle configuration files
docs/               Documentation
templates/          Import templates for manual data upload
tests/              End-to-end tests

## Getting Started

See docs/school_deployment_guide.md to deploy to a school server.
See docs/central_server_guide.md to set up the central server.
See docs/admin_user_guide.md to manage schools and settings.

## Brand Colors

Primary green:     #81BC00
Primary blue:      #375C7A
White:             #FFFFFF
Secondary purple:  #943266

## License

Camara Education Ethiopia. All rights reserved.
# CDLAID Learning Analytics API

## Local Development Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd Digital-Learning-Analytics-Project
