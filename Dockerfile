FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all application files
COPY . /app

# Create necessary directories for operation
RUN mkdir -p temp_uploads temp_outputs

# Expose the Flask port
EXPOSE 5000

# Run the application
# Note: Dependencies are installed by app.py on startup
CMD ["python", "app.py"]
