# Technician Portal Deployment Guide

This guide will help you deploy your Technician Portal application to a free hosting platform.

## Prerequisites

Make sure you have the following:
- Git installed on your computer
- A GitHub account
- A Railway, Render, or Heroku account (we'll focus on Railway as they have a generous free tier)

## Required Dependencies

When setting up your deployment, make sure these dependencies are installed:

```
flask
flask-login
flask-sqlalchemy
flask-wtf
gunicorn
matplotlib
numpy
pandas
psycopg2-binary
email-validator
python-dotenv
```

## Deployment Steps for Railway

Railway offers a free tier that includes PostgreSQL and web hosting.

1. **Create a Railway account**
   - Go to [Railway.app](https://railway.app/)
   - Sign up using GitHub or email

2. **Download your code from Replit**
   - Click on the three dots (menu) in the Replit interface
   - Select "Download as ZIP"
   - Extract the ZIP file on your computer

3. **Create a new GitHub repository**
   - Go to GitHub and create a new repository
   - Upload all the files from your extracted ZIP

4. **Create a .env file** (add this to .gitignore)
   ```
   DATABASE_URL=postgres://postgres:password@localhost:5432/utilities_db
   FLASK_SECRET_KEY=your_secret_key
   ```

5. **Add a Procfile for deployment**
   ```
   web: gunicorn main:app
   ```

6. **Deploy on Railway**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Add a PostgreSQL plugin from the "New" menu
   - Railway will automatically detect your Python project and build it

7. **Set Environment Variables**
   - In your Railway project, go to the "Variables" tab
   - Railway automatically sets DATABASE_URL when you add PostgreSQL
   - Add FLASK_SECRET_KEY with a secure random value

8. **Run Database Migrations**
   - Under the "Deployments" tab, you can access a shell
   - Run: `python -c "from app import db; db.create_all()"`

9. **Visit Your Application**
   - Once deployed, Railway will provide a public URL for your application

## Deployment Steps for Render

Render is another platform with a free tier:

1. **Sign up for Render**
   - Go to [Render.com](https://render.com/)
   - Create an account

2. **Create a new Web Service**
   - Click "New" → "Web Service"
   - Connect to your GitHub repository

3. **Configure Build Settings**
   - Name: TechnicianPortal
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app`

4. **Add Environment Variables**
   - Add DATABASE_URL (you'll need to create a PostgreSQL database)
   - Add FLASK_SECRET_KEY

5. **Deploy Your Application**
   - Click "Create Web Service"

## Troubleshooting

- **Database connection issues**: Make sure your DATABASE_URL is correctly formatted
- **Port binding errors**: Ensure your app is binding to the port specified in the environment (use `os.getenv("PORT", 5000)`)
- **Missing dependencies**: Check if all required packages are listed in requirements.txt

## Local Development

You can run your application locally with:

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Set up a local PostgreSQL database
5. Create a .env file with your DATABASE_URL and FLASK_SECRET_KEY
6. Run the application: `python main.py`