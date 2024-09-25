# Start from a base image with Python
FROM python:3.9-slim

# Install any necessary system dependencies for Chrome
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o google-chrome.deb && \
    apt-get update && \
    apt-get install -y ./google-chrome.deb && \
    rm google-chrome.deb

# Set the working directory
WORKDIR /src

# Copy the requirements file
COPY requirements.txt /src

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /src

# Command to run the application
CMD ["python", "airkaz-bot.py"]
