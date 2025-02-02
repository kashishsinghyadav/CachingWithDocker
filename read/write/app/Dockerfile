# Use official Python image
FROM python

# Set working directory
WORKDIR /app


# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run FastAPI server
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
