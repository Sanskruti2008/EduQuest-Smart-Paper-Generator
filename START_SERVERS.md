# Starting EduQuest.ai Servers

## Quick Start (Windows)

### Method 1: PowerShell Commands

**Backend Server (Port 5000):**
```powershell
cd "c:\Users\sanskruti\OneDrive\Desktop\EduQuest.ai\backend"
python server.py
```

**Frontend Server (Port 3000):**
```powershell
cd "c:\Users\sanskruti\OneDrive\Desktop\EduQuest.ai"
npm run dev
```

### Method 2: One-Click Start
Run these commands in separate PowerShell windows:

```powershell
# Start Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\sanskruti\OneDrive\Desktop\EduQuest.ai\backend'; python server.py"

# Start Frontend (wait 2 seconds first)
Start-Sleep -Seconds 2; Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:\Users\sanskruti\OneDrive\Desktop\EduQuest.ai'; npm run dev"
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Health Check**: http://localhost:5000/api/health

## Stopping Servers

Press `Ctrl+C` in each server window, or run:
```powershell
Get-Process | Where-Object { $_.ProcessName -eq 'python' -or $_.ProcessName -eq 'node' } | Stop-Process -Force
```

## Troubleshooting

**Port already in use:**
```powershell
# Kill process on port 5000
Get-NetTCPConnection -LocalPort 5000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }

# Kill process on port 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

**Backend not responding:**
- Check if Tesseract OCR is installed: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- Verify Python environment has all dependencies: `pip install -r backend/requirements.txt`

**Frontend build errors:**
- Clear node modules: `Remove-Item node_modules -Recurse -Force; npm install`
- Clear cache: `npm cache clean --force`

## Recent Fixes

✅ Removed debug mode (server no longer crashes from reloader)
✅ Cleaned up excessive print statements
✅ Fixed frontend-backend data structure mismatch
✅ Added proper error handling for screenshot PDFs
✅ Simplified upload response handling

## Notes

- Backend runs without debug mode to prevent reloader crashes
- Frontend uses Vite for hot module replacement
- Upload only text-based PDFs (not screenshots) for best results
