# Use our official image as base
FROM facturxengine/facturx-engine:latest

# Switch to root to install demo dependencies
USER root
RUN pip install gradio httpx

# Create a demo user to match HF requirements (user 1000)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set working directory to the user's home
WORKDIR $HOME/app

# Copy the demo application code
COPY --chown=user . $HOME/app

# Expose the standard HF Space port
EXPOSE 7860

# CMD launch script
CMD ["python", "app.py"]
