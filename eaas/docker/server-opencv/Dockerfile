FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy your Python script and any required files into the container
COPY src.py /app/
COPY requirements.txt /app/
COPY space_sample.mp4 /app/

# Install env
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

# Install any required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define an entry point (the script to run when the container starts)
ENTRYPOINT ["python", "src.py"]

# RUN -> docker run -it --rm -p 8888:8888 opencv_server (2)


