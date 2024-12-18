# Stage 1: Build the React frontend
FROM --platform=linux/amd64 node:16

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install all dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port used by the React development server
EXPOSE 3000

# Command to run in development mode
CMD ["npm", "start"]

