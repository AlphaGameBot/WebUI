# Use the official Python image from the Docker Hub
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Install Tailwind CSS
RUN npm install -D tailwindcss

# Build the Tailwind CSS file
RUN npx tailwindcss -i ./src/input.css -o ./dist/tailwind.css

# Command to run the application
CMD ["python", "app.py"]
# Use multi-stage builds to reduce the final image size
# Stage 1: Build Tailwind CSS using a Node.js image
FROM node:18-alpine AS tailwind-builder

WORKDIR /app

# Copy only the necessary files to build Tailwind CSS
COPY package.json package-lock.json input.css ./
COPY templates /app/src/templates
# Install dependencies and build Tailwind CSS
RUN npm install
RUN npx tailwindcss -i ./input.css -o ./dist/tailwind.css --content './src/**/*.html'

# Stage 2: Use the official Python image from the Docker Hub
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Copy the built Tailwind CSS file from the previous stage
COPY --from=tailwind-builder /app/dist/tailwind.css ./static/tailwind.css

ENV FLASK_APP=main

# Command to run the application
CMD ["flask", "run"]
