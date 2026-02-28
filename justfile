# TranslateFlow Justfile
# Common commands for development and deployment

# Default recipe to show help
default:
    @just --list

# Install dependencies
install:
    cd Tools/WebServer && npm install
    uv sync

# Build frontend
build:
    cd Tools/WebServer && npm run build

# Start web server (development)
start:
    @echo "Starting TranslateFlow web server..."
    cd Tools/WebServer && npm run dev &

# Start web server (production mode)
start-prod:
    @echo "Starting TranslateFlow web server in production mode..."
    cd Tools/WebServer && npm run preview &

# Stop web server
stop:
    @echo "Stopping TranslateFlow web server..."
    pkill -f "vite" || true
    pkill -f "uvicorn" || true

# Start backend API server
start-api:
    @echo "Starting TranslateFlow API server..."
    cd {{ justfile_directory() }} && python -m uvicorn Tools.WebServer.web_server:app --host 0.0.0.0 --port 8000 &

# Stop backend API server
stop-api:
    @echo "Stopping TranslateFlow API server..."
    pkill -f "web_server" || true

# Run database migrations
migrate:
    @echo "Running database migrations..."
    @cd {{ justfile_directory() }} && python -c "from ModuleFolders.Infrastructure.Database.pgsql import database; from ModuleFolders.Service.Auth.models import User; from ModuleFolders.Service.Team.team_repository import Team, TeamMember; database.connect(); database.create_tables([User, Team, TeamMember]); print('Migration completed!'); database.close()"

# Reset database (drops all tables)
reset-db:
    @echo "Resetting database..."
    @echo "This will delete all data! Are you sure? (y/N)"
    @cd {{ justfile_directory() }} && python -c "from ModuleFolders.Infrastructure.Database.pgsql import database; from ModuleFolders.Service.Auth.models import User; from ModuleFolders.Service.Team.team_repository import Team, TeamMember; database.connect(); database.drop_tables([User, Team, TeamMember]); print('Database reset!'); database.close()"

# Start all services (frontend + backend)
start-all: start start-api
    @echo "All services started!"
    @echo "Frontend: http://localhost:4200"
    @echo "Backend API: http://localhost:8000"

# Stop all services
stop-all: stop stop-api
    @echo "All services stopped!"

# Restart all services
restart: stop-all start-all

# Development mode with hot reload
dev: install build start
    @echo "Starting development mode..."

# Run tests
test:
    echo "No tests configured yet"

# Lint code
lint:
    cd Tools/WebServer && npx eslint src/

# Format code
format:
    cd Tools/WebServer && npx prettier --write src/
