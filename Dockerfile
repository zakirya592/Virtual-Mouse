FROM python:3.10

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    xvfb \
    x11-utils \
    libopencv-dev \
    python3-opencv \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install mediapipe==0.10.13
RUN pip install -r requirements.txt

EXPOSE 7860

# Set display environment variable
ENV DISPLAY=:99

CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & python app.py"]