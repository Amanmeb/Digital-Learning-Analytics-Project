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
