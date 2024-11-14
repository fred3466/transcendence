# Use the official Vault image from HashiCorp
FROM hashicorp/vault:latest

# Set the working directory inside the container
WORKDIR /vault

# Install curl using Alpine's package manager (apk)
RUN apk add --no-cache curl

# Copy all files from the host's current directory to the /vault directory in the container
COPY . .

# Make the entrypoint.sh script executable
RUN chmod +x /vault/entrypoint.sh

# Set the entrypoint to the custom script
ENTRYPOINT ["/vault/entrypoint.sh"]