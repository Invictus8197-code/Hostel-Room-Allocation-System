@echo off
echo ==========================================
echo Starting Smart Hostel Room Allocation System
echo ==========================================
echo.
echo Activating Virtual Environment...
call .venv\Scripts\activate

echo Applying Migrations (if any)...
cd backend
python manage.py migrate

echo Seeding Data (if needed)...
python manage.py seed_data

echo.
echo ==========================================
echo System is starting! 
echo The frontend and backend are both served by this command.
echo A new browser window will open automatically.
echo ==========================================
echo.

start http://127.0.0.1:8000/
python manage.py runserver
