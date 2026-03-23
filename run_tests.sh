#!/bin/bash
source .venv/bin/activate
python -m pytest tests/test_energy_schedule.py -v
