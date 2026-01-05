#!/bin/bash

# Build Electron Desktop App

set -e

echo "Building Riddle Master Desktop App..."

# Navigate to frontend
cd "$(dirname "$0")/../frontend"

# Install electron dependencies if not present
if ! grep -q "electron" package.json; then
  echo "Installing Electron dependencies..."
  yarn add --dev electron electron-builder concurrently wait-on cross-env
fi

# Build React app
echo "Building React app..."
yarn build

# Create electron main file if it doesn't exist
if [ ! -f "electron.js" ]; then
  echo "Creating electron.js..."
  cat > electron.js << 'EOF'
const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  win.loadURL(
    isDev
      ? 'http://localhost:3000'
      : `file://${path.join(__dirname, 'build/index.html')}`
  );

  if (isDev) {
    win.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
EOF
fi

# Update package.json with electron scripts
echo "Configuring package.json for Electron..."
node -e "
const fs = require('fs');
const pkg = JSON.parse(fs.readFileSync('package.json'));
pkg.main = 'electron.js';
pkg.homepage = './';
pkg.build = {
  appId: 'com.riddlemaster.app',
  productName: 'Riddle Master',
  files: ['build/**/*', 'electron.js', 'node_modules/**/*'],
  directories: { buildResources: 'assets' },
  mac: { category: 'public.app-category.games' },
  win: { target: 'nsis' },
  linux: { target: 'AppImage' }
};
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2));
"

# Build electron app
echo "Building Electron executable..."
yarn electron-builder

echo "✅ Desktop app built successfully!"
echo "📦 Output: frontend/dist/"