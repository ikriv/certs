FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy certcore package
COPY certcore /app/certcore

# Copy application code
COPY server/app.py .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
