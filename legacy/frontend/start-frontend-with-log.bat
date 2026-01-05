@echo off
:: Frontend logging wrapper
cd /d "%~1"
set PORT=3000
set BROWSER=none
yarn start > frontend.log 2>&1
