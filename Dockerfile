# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app/

# Expose any required ports (if necessary)
EXPOSE 9092 4002

# Define the command to run the application
CMD ["python", "stock_app.py"]

