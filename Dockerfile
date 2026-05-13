# Use a Python image that includes uv or install it manually
FROM python:3.12-slim

# Install uv directly from the official binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startups
ENV UV_COMPILE_BYTECODE=1
# Prevent uv from looking for a project root (useful for simple scripts)
ENV UV_PROJECT_ENVIRONMENT=/venv

# Copy only dependency files first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-dev

# Copy the rest of your 50+ files
COPY . .

# Ensure the virtualenv bin is in the path
ENV PATH="/app/.venv/bin:$PATH"

# Run your script
CMD ["uv", "run", "docker_entrypoint.py"]