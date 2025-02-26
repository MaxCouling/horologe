FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/icons

# Set environment variables
ENV FLASK_APP=app.py
ENV VAPID_PUBLIC_KEY=BPnb_ocJUtpagevTb5bz-lQAw4xyKZWmoaTO4tdaLUpBPQyADzJGQW17R4Ib0BsGRodTZT1MkQ8xuS8kXyupthQ=
ENV VAPID_PRIVATE_KEY=MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgk5wIH6NnHoW9WhMO6aaVFggUuxl4Ps-Frk8TTWKL7MmhRANCAAT52_6HCVLaWoHr02-W8_pUAMOMcimVpqGkzuLXWi1KQT0MgA8yRkFte0eCG9AbBkaHU2U9TJEPMbkvJF8rqbYU

EXPOSE 5000

CMD ["python", "app.py"]
