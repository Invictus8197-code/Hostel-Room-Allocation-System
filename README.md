# Smart Hostel Room Allocation & Vacancy Optimizer

## Overview
A full-stack hostel room allocation system powered by Google OR-Tools (CP-SAT), React, and Django. Designed to optimally allocate student room requests while enforcing hard constraints (gender separation, maximum capacity) and maximizing preference satisfaction (AC/Non-AC, room type).

## Features
- **Intelligent Optimizer**: CP-SAT engine maximizes allocations and preference matches.
- **Transaction-Safe Workflow**: Draft -> Approve -> Commit state machine.
- **Analytics Dashboard**: Real-time occupancy, vacancy, and utilization tracking.
- **What-If Simulations**: Test future scenarios without mutating production data.
- **Role-Based Auth**: Distinct features for ADMIN, WARDEN, and STUDENT roles.

## One-Click Demonstration Startup
This repository comes with a one-click startup script configured for Phase 8 demonstration.

1. Ensure Python 3.11+ and Node.js are installed.
2. Double-click the **`start_demo.bat`** file in the project root.
3. The script will:
   - Activate the Python virtual environment.
   - Run migrations.
   - Seed realistic demo data (Hostels, 50 Beds, 65 Students).
   - Start the unified backend and frontend server.
   - Automatically open the dashboard in your default browser at `http://127.0.0.1:8000/`.

## Manual Setup
If you prefer not to use the automated script:
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py seed_data
python backend/manage.py runserver
```

## Running Tests
To run the full suite (including End-to-End simulation tests):
```bash
python backend/manage.py test backend.apps
```

## Demo Flow Guide
1. **Login:** Use credentials `admin` / `admin`.
2. **Dashboard:** View initial vacancy states (65 eligible students vs 50 beds).
3. **Run Optimizer:** Navigate to Allocations and generate a Draft Run.
4. **Review Constraints:** Verify 50 students were allocated, leaving 15 unallocated due to strict capacity constraints.
5. **Approve & Commit:** Commit the draft securely.
6. **Analytics:** Revisit the Dashboard to see 100% occupancy for the 50 beds.
7. **Simulation:** Run a "What-If" scenario to verify future possibilities without mutating the committed allocations.
