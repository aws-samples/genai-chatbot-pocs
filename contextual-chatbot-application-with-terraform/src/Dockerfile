FROM python:3.12-slim

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8501

# Create a non-root user
RUN groupadd --gid 1000 tfgroup && useradd --uid 1001 --gid 1000 -m tfuser

# Switch to the non-root user
USER tfuser

# Set the working directory
WORKDIR /app

COPY --chown=tfuser:tfgroup *.py .
COPY --chown=tfuser:tfgroup *.txt .

RUN pip3 install --user -r requirements.txt

# Add local user bin to PATH
ENV PATH="/home/tfuser/.local/bin:${PATH}"

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]