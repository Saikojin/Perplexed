FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Copy application
COPY . .

# Expose port
EXPOSE 3000

# Run application
CMD ["yarn", "start"]