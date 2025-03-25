# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app:create_app
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]

# Generated by Copilot
