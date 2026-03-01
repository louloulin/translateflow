# Docker Volume Permission Configuration

## Problem

When mounting host directories to Docker containers, permission conflicts occur because:
- Docker container runs as `translateflow` user (UID 1000, GID 1000)
- Host directories may be owned by root or other users
- Container cannot write to mounted volumes

## Solution

### Method 1: Automated Setup (Recommended)

Run the setup script before starting the container:

```bash
./setup-docker-volumes.sh
```

This script will:
- Create required directories (output, updatetemp, data, Resource/profiles)
- Set ownership to UID 1000:1000 (translateflow user)
- Set correct permissions (755 for directories, 644 for files)

### Method 2: Manual Setup

If you prefer manual setup:

```bash
# Create directories
mkdir -p output updatetemp data Resource/profiles

# Set ownership to translateflow user (UID 1000, GID 1000)
sudo chown -R 1000:1000 output updatetemp data Resource

# Set directory permissions
chmod -R 755 output updatetemp data Resource
find Resource -type d -exec chmod 755 {} \;
find Resource -type f -exec chmod 644 {} \;
```

### Method 3: Docker Compose User Mapping

The `docker-compose.local.yml` includes:

```yaml
user: "1000:1000"  # Run as translateflow user
volumes:
  - ./Resource:/app/Resource  # Mount Resource directory
```

This ensures the container runs with the same UID as the host user.

## Directory Structure After Setup

```
drwxr-xr-x  1000:1000  output/
drwxr-xr-x  1000:1000  updatetemp/
drwxr-xr-x  1000:1000  data/
drwxr-xr-x  1000:1000  Resource/
├── drwxr-xr-x  1000:1000  profiles/
├── -rw-r--r--  1000:1000  platforms/preset.json
└── -rw-r--r--  1000:1000  config.json (created at runtime)
```

## Verifying Permissions

Check permissions with:

```bash
ls -la output updatetemp data Resource
```

All directories should show `1000:1000` ownership.

## Troubleshooting

### Permission Denied Errors

If you see "Permission denied" errors:

1. Stop the container:
   ```bash
   docker-compose -f docker-compose.local.yml down
   ```

2. Fix permissions:
   ```bash
   sudo chown -R 1000:1000 output updatetemp data Resource
   ```

3. Restart the container:
   ```bash
   docker-compose -f docker-compose.local.yml up -d
   ```

### Cannot Write to Resource Directory

If init_config() fails to create config files:

```bash
# Check Resource permissions
ls -la Resource

# Fix if needed
sudo chown -R 1000:1000 Resource
chmod -R 755 Resource
find Resource -type f -exec chmod 644 {} \;
```

## Production Deployment

For production, ensure:

1. Host directories owned by UID 1000:1000
2. Resource directory mounted for persistent configuration
3. Regular backups of Resource/ and data/ directories

Example production docker-compose:

```yaml
volumes:
  - /var/lib/translateflow/output:/app/output
  - /var/lib/translateflow/data:/app/data
  - /etc/translateflow/Resource:/app/Resource
```

With host directories pre-created:

```bash
sudo mkdir -p /var/lib/translateflow/{output,data}
sudo mkdir -p /etc/translateflow/Resource/profiles
sudo chown -R 1000:1000 /var/lib/translateflow /etc/translateflow
```
