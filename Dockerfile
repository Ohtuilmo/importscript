# Set base image
FROM python:3.9

# Set timezone and working directory for the app in container
ENV TZ="Europe/Helsinki"

# Update package lists and install rsync
RUN apt-get update && apt-get install -y rsync && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the requirements.txt file and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Create data directories
RUN mkdir -p data

# Copy the rest of the project files to the working directory
COPY . .

# Launch application
CMD ["python3", "index.py"]