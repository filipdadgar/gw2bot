# GW2 Bot on Windows: Native Setup Guide

This guide walks you through setting up and running the GW2 Bot directly on Windows without Docker, from cloning the repository to running your first automated farm cycle.

**Prerequisites:**
- Windows 10 or later
- Guild Wars 2 installed and ready to run
- ~5 minutes to complete

---

## Step 1: Clone the Repository

Open **PowerShell** or **Command Prompt** and clone the repo:

```powershell
git clone https://github.com/yourusername/gw2bot.git
cd gw2bot
```

(If you don't have Git installed, [download it here](https://git-scm.com/download/win))

---

## Step 2: Install Python 3.12.5

1. Download Python 3.12.5 from [python.org](https://www.python.org/downloads/)
2. **Important**: During installation, check the box **"Add Python to PATH"**
3. Verify installation:

```powershell
python --version
```

Should output: `Python 3.12.5`

---

## Step 3: Create and Activate Virtual Environment

Still in the `gw2bot` directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

You should see `(.venv)` at the start of your PowerShell prompt.

**If you get an execution policy error**, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then retry the activate command.

---

## Step 4: Install Dependencies

With the virtual environment active:

```powershell
pip install --upgrade pip
pip install -e .
```

This installs FastAPI, Pydantic, pytest, and all bot dependencies.

If you also want development tools (pytest, ruff, mypy), run:

```powershell
pip install -e ".[dev]"
```

---

## Step 5: Setup Environment Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Because `.env.example` is shared with Docker, update the data path for native Windows:

```powershell
(Get-Content .env) -replace '^GW2_DATA_DIR=.*', 'GW2_DATA_DIR=data' | Set-Content .env
```

This creates a `.env` file with mission-mode defaults already enabled:
- **Auto-start runs**: `GW2_AUTOSTART_RUN_ENABLED=true` ✅
- **Auto-retrain**: `GW2_TRAINING_AUTO_RETRAIN_ENABLED=true` ✅
- **Runtime policy**: `GW2_RUNTIME_POLICY_ENABLED=true` ✅
- **Runtime input execution**: `GW2_RUNTIME_INPUT_ENABLED=true` ✅
- **Native data path**: `GW2_DATA_DIR=data` ✅

You can edit `.env` in Notepad if you need to adjust values, but defaults are production-ready.

---

## Step 6: Start Guild Wars 2

1. Launch GW2 on your Windows machine
2. Log in and get to your character on a farming-suitable map
3. **Keep the GW2 window fully visible** (host bridge needs screen access for frame capture)

---

## Step 7: Run the Bot

With the virtual environment still active and `.env` in place, start the FastAPI server:

```powershell
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

You should see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     [Autostart] Mission mode activated; starting discovery-first run...
```

---

## Step 8: Verify the Bot is Running

Open a **new PowerShell window** (keep the first one running) and check the bot status:

```powershell
curl http://127.0.0.1:8000/v1/run/status
```

Expected response (after a few seconds):

```json
{
  "cycle_id": "cycle-xyz123",
  "route_id": "route-discovery-001",
  "status": "running",
  "current_waypoint_index": 0,
  "started_at_utc": "2026-04-01T12:34:56Z",
  "last_error": null
}
```

If status is `running`, the bot has successfully started a farm cycle! 🎉

---

## Step 9: Monitor the Run

Watch the logs in your original PowerShell window. You should see:

```
INFO: Starting discovery-first run with auto_discover_if_missing=True
INFO: Route discovery complete; 8 waypoints identified
INFO: Runtime loop started; emitting policy signals every 100ms
INFO: Cycle progress: waypoint 0/8 (harvest success: 2/2)
```

The bot will:
1. **Discover** waypoints on your current map
2. **Navigate** to each waypoint
3. **Harvest** available resources
4. **Collect policy signals** from your gameplay
5. **Retrain** the policy model every 5 minutes (default)

---

## Step 10: Stop the Bot

Press **Ctrl+C** in the FastAPI terminal:

```
^C
INFO: Shutting down
```

This gracefully stops the current farm cycle.

---

## Mission Mode Behavior

With default `.env` settings, the bot operates in **mission mode**:

✅ **Autostart**: Bot automatically starts a run on launch  
✅ **Continuous Learning**: Collects policy signals from every action  
✅ **Automatic Retraining**: Retrains the policy model on schedule  
✅ **Runtime Input Execution**: Sends bounded in-game key taps for selected actions  
✅ **Policy-Guided Actions**: Applies learned behaviors at runtime  

You don't need to make API calls—the bot learns and improves automatically.

---

## API Reference (Optional)

You can manually control the bot via REST APIs. Open another PowerShell and:

### Check Route List
```powershell
curl http://127.0.0.1:8000/v1/routes
```

### Get Cycle Summary
```powershell
curl http://127.0.0.1:8000/v1/cycle/summary
```

### Get Policy Versions
```powershell
curl http://127.0.0.1:8000/v1/training/policy/versions
```

### Pause the Run
```powershell
curl -X POST http://127.0.0.1:8000/v1/run/pause
```

### Resume the Run
```powershell
curl -X POST http://127.0.0.1:8000/v1/run/resume
```

Full API docs available at: `http://127.0.0.1:8000/docs`

---

## Troubleshooting

### Bot Starts but Status Shows `idle`
- Ensure GW2 is running and fully visible
- Check that the Windows is not in sleep mode
- Verify `.env` has `GW2_AUTOSTART_RUN_ENABLED=true`

### "Module not found" Error
- Verify virtual environment is active: `(.venv)` should appear in prompt
- Re-run: `pip install -e .`

### Port 8000 Already in Use
If another app is using port 8000, specify a different port:
```powershell
uvicorn src.api.main:app --host 0.0.0.0 --port 8001
```

Then access APIs at `http://127.0.0.1:8001`

### Host Bridge Warnings in Logs
If you see "Capture unavailable", the Windows host bridge may not have screen access. Ensure:
- GW2 window is fully visible (not minimized)
- No screensaver is active
- No other full-screen application is covering the window

### Validate In-Game Input Execution
Run this command and ensure `bridge_enabled` is `1.0` with non-zero frame sizes:

```powershell
Get-Content .\data\telemetry\policy-signals.jsonl -Tail 10
```

---

## Next Steps

1. **Run for 5+ minutes** to collect initial policy signals
2. **Check telemetry**: `curl http://127.0.0.1:8000/v1/cycle/summary`
3. **Review learned routes**: `curl http://127.0.0.1:8000/v1/routes`
4. **Monitor policy training**: Watch logs for "Policy model updated" messages

For advanced configuration and Docker setup, see [gw2bot-runbook.md](gw2bot-runbook.md).
