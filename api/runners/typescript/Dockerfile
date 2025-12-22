FROM node:20-slim

WORKDIR /app

# Install TypeScript compiler
RUN npm install -g typescript

# Non-root user (important)
RUN useradd -m runner
USER runner

CMD ["bash"]
