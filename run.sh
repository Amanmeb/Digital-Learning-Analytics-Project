#!/bin/bash

export PYTHONPATH="$(pwd)/backend"

uvicorn api.main:app --reload
