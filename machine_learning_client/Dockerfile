# Using the slim version of the Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary system libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the local directory contents to the container's working directory
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV MONGO_URI=ENV MONGO_URI=mongodb+srv://William:Wl1234567890@cluster0.mu4sweo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&ssl=false

# Make port available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
