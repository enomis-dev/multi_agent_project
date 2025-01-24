# Use an official Python runtime as a parent image
FROM python:3.10

# Install required dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Set the working directory to /app
WORKDIR /app/src

# Copy the Python application files to the container's working directory
COPY src /app/src

# Expose port 5000 for the Flask application
EXPOSE 5000

# Run the Flask application
CMD ["python", "app.py"]
