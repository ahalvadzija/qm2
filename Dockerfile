# Use a lightweight Python base image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy only the files needed for metadata and dependencies
COPY pyproject.toml README.md LICENSE ./

# 2. Copy the source code (THIS WAS MISSING in the previous step)
# We need the folder structure for pip install to work
COPY src/ ./src/

# 3. Install the package
RUN pip install --no-cache-dir .

# 4. Copy everything else (docs, examples, tests) if needed
# though .dockerignore will filter most of it
COPY . .

# Create the data directory
RUN mkdir -p /root/.local/share/qm2

# Define the command to run the application
ENTRYPOINT ["qm2"]