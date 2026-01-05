# Building Standalone Applications

This guide covers different methods to package Riddle Master as a standalone application.

## Option 1: Desktop App with Electron

### Prerequisites
- Node.js 18+
- Yarn
- Built React app

### Build Process

```bash
cd frontend

# Install Electron dependencies
yarn add --dev electron electron-builder electron-is-dev concurrently wait-on

# Build React app
yarn build

# Build desktop app
yarn electron-builder --mac --windows --linux
```

### Output
- **macOS**: `frontend/dist/Riddle Master.dmg`
- **Windows**: `frontend/dist/Riddle Master Setup.exe`
- **Linux**: `frontend/dist/Riddle Master.AppImage`

### Configuration

Add to `frontend/package.json`:

```json
{
  "main": "electron.js",
  "homepage": "./",
  "scripts": {
    "electron": "electron .",
    "electron:build": "electron-builder"
  },
  "build": {
    "appId": "com.riddlemaster.app",
    "productName": "Riddle Master",
    "files": [
      "build/**/*",
      "electron.js",
      "node_modules/**/*"
    ],
    "directories": {
      "buildResources": "assets"
    },
    "mac": {
      "category": "public.app-category.games",
      "icon": "assets/icon.icns"
    },
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "linux": {
      "target": "AppImage",
      "icon": "assets/icon.png"
    }
  }
}
```

### Bundling Backend

To include backend in Electron app:

1. **Package backend as executable** (see Option 2)
2. **Place in Electron resources**:
   ```javascript
   // electron.js
   const { spawn } = require('child_process');
   const path = require('path');
   
   // Start backend
   const backendPath = path.join(__dirname, 'resources', 'riddle-backend');
   const backend = spawn(backendPath);
   
   // Create window after backend starts
   setTimeout(createWindow, 3000);
   ```

## Option 2: Backend Executable with PyInstaller

### Prerequisites
- Python 3.11+
- Virtual environment
- PyInstaller

### Build Process

```bash
cd backend
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Create spec file
pyi-makespec --onefile --name riddle-backend server.py

# Edit spec file to include data files
# Add to Analysis():
#   datas=[('.env', '.'), ('*.py', '.')],
#   hiddenimports=['emergentintegrations', 'motor'],

# Build
pyinstaller riddle-backend.spec --clean
```

### Output
- `backend/dist/riddle-backend` (executable)

### Running Standalone Backend

```bash
# Set environment variables
export MONGO_URL=mongodb://localhost:27017
export DB_NAME=riddle_game_db
export JWT_SECRET_KEY=your-secret-key
export ENCRYPTION_KEY=your-encryption-key-32chars!!
export EMERGENT_LLM_KEY=sk-emergent-your-key

# Run
./dist/riddle-backend
```

### Issues & Solutions

**MongoDB Connection**: Requires MongoDB installed separately or use embedded database

**Large File Size**: ~100MB+ due to Python dependencies
- Solution: Use Docker instead for server deployment

**Missing Modules**: Add to `hiddenimports` in spec file

## Option 3: Docker Container

### Single Container Build

```dockerfile
# Multi-stage build
FROM node:18-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install
COPY frontend/ ./
RUN yarn build

FROM python:3.11-slim
WORKDIR /app

# Install MongoDB (embedded)
RUN apt-get update && apt-get install -y mongodb

# Install backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-build /app/build ./frontend/build

# Expose ports
EXPOSE 8001 27017

# Start services
CMD mongod --fork --logpath /var/log/mongodb.log && \
    uvicorn server:app --host 0.0.0.0 --port 8001
```

Build and run:
```bash
docker build -t riddle-master .
docker run -p 8001:8001 -p 3000:3000 riddle-master
```

## Option 4: Progressive Web App (PWA)

Convert to installable web app:

### 1. Update `frontend/public/manifest.json`:

```json
{
  "short_name": "Riddle Master",
  "name": "Riddle Master - Daily Puzzles",
  "icons": [
    {
      "src": "icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#1e293b",
  "background_color": "#0f172a"
}
```

### 2. Add Service Worker

Create `frontend/public/service-worker.js`:

```javascript
const CACHE_NAME = 'riddle-master-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

### 3. Register in `frontend/src/index.js`:

```javascript
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js');
  });
}
```

Users can now "Install" the app on mobile/desktop!

## Option 5: Native Mobile (React Native)

For true mobile apps, consider rewriting frontend with React Native:

```bash
npx react-native init RiddleMaster
# Port React components to React Native
# Connect to same backend API
```

## Comparison

| Method | Platform | Size | Offline | Complexity |
|--------|----------|------|---------|------------|
| Electron | Desktop | ~150MB | Full | Medium |
| PyInstaller | Server | ~100MB | Backend only | Low |
| Docker | Any | ~500MB | Full | Low |
| PWA | Web | ~2MB | Partial | Low |
| React Native | Mobile | ~50MB | Full | High |

## Recommendations

- **Desktop users**: Electron + embedded backend
- **Server deployment**: Docker
- **Mobile users**: PWA (quick) or React Native (best)
- **Offline play**: Electron or React Native
- **Quick distribution**: PWA

## Next Steps

1. Choose deployment method
2. Follow build steps
3. Test on target platform
4. Sign/notarize executables (macOS/Windows)
5. Distribute via website or app stores
