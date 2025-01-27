# Use an official Python runtime as a parent image
FROM python:3.10

# Install required dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Set the working directory to /app
WORKDIR /app/src

# Copy the Python application files to the container's working directory
COPY src /app/src

# Expose port 8501 for the Streamlit application
EXPOSE 8501

# Run the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

