# Scripts Directory

Utility scripts for development, testing, and deployment.

## Available Scripts

### Development
- **`dev.sh`** - Start development server with hot reload
  ```bash
  ./scripts/dev.sh
  ```

### Database
- **`migrate.sh`** - Run database migrations
  ```bash
  ./scripts/migrate.sh
  ```

### Testing
- **`test.sh`** - Run tests with coverage
  ```bash
  ./scripts/test.sh
  ```

### Deployment
- **`build.sh`** - Production build script (used by Render)
  ```bash
  ./scripts/build.sh
  ```

## Making Scripts Executable

On Linux/Mac:
```bash
chmod +x scripts/*.sh
```

On Windows (Git Bash):
```bash
bash scripts/dev.sh
```

## Usage Examples

**Start development:**
```bash
./scripts/dev.sh
```

**Run migrations:**
```bash
./scripts/migrate.sh
```

**Run tests:**
```bash
./scripts/test.sh
```

**Production build:**
```bash
./scripts/build.sh
```
