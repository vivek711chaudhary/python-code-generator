FROM python:3.10-slim

# Create a non-root user to run the code
RUN adduser --disabled-password --gecos '' pythonuser

# Create and set the working directory
WORKDIR /code

# Set the default Python path to the working directory
ENV PYTHONPATH=/code

# Remove unnecessary packages and tools
RUN apt-get update && \
    apt-get purge -y --auto-remove curl wget netcat ssh git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Disable networking capabilities
RUN rm -rf /bin/nc /bin/netcat /usr/bin/nc /usr/bin/netcat /bin/ping /usr/bin/ping 2>/dev/null || true

# Limit writable directories
RUN mkdir -p /tmp/python_output && \
    chown pythonuser:pythonuser /tmp/python_output && \
    chmod 700 /tmp/python_output

# Set environment to disallow network access and prevent certain operations
ENV PYTHONNOUSERSITE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TMPDIR=/tmp/python_output \
    HOME=/tmp/python_output

# Switch to non-root user
USER pythonuser

# Copy a script that will be used to run the Python code
COPY --chown=pythonuser:pythonuser dockerfile/run_code.sh /usr/local/bin/run_code.sh
RUN chmod +x /usr/local/bin/run_code.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/run_code.sh"]

# Default command (will be overridden at runtime)
CMD ["--version"] 