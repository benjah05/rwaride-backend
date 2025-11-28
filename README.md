# RWARIDE

## Project Overview
RwaRide is a Simple, safe, efficient, and community-driven carpooling platform. It will help reduce travel costs, save time, and build connections while supporting sustainable mobility in Rwanda.

## Core Functionality
- **User Authentication & Authorization:**
    * Secure user registration and login using JWT (JSON Web Tokens).
    * Protected routes ensuring only authenticated users can perform certain actions.

## Technologies Used
- **Backend Framework:** Flask
- **ORM (Object-Relational Mapper):** SQLAlchemy
- **Database:** MySQL
- **Authentication:** Flask-JWT-Extended

## Setup and Installation
Step-by-step instructions on how to get the rwaride-backend running locally.
1. **Prerequisites:**
    - Python 3.x (Ensure you have a recent version like python 3.11.5, but 3.8+ is also fine)
    - MySQL Server (and optionally MySQL Workbench for database management)
    - pip: Python package installer (usually comes with Python)
2. **Clone the Repository:**
```
git clone https://github.com/benjah05/rwaride-backend.git
cd rwaride-backend
```
3. **Create And Activate Virtual Environment:**
```
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```
4. **Install Dependencies:**
```
pip install -r requirements.txt
# If requirements.txt is not present, run:
# pip install flask flask-sqlalchemy pymysql flask-jwt-extended
```
After installing, you can create a *requirements.txt* file by running *pip freeze > requirements.txt* in your activated virtual environment for future use.