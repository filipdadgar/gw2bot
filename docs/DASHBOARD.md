# GW2 Bot Web Dashboard

A modern, web-based control interface for the GW2 Bot that requires no focus stealing. Unlike PowerShell terminal commands, the dashboard runs in a browser and doesn't interrupt your GW2 gameplay.

## Access

Open your browser and navigate to:

- **Local access**: `http://localhost:8000`
- **Network access**: `http://<your-machine-ip>:8000`

## Features

### Run Control
- **Start/Stop/Pause**: Control bot operations without switching windows
- **Real-time Status**: View current cycle, route, and waypoint
- **Auto-retrain**: Background policy training every 300 seconds

### Policy Management
- **Train Now**: Trigger model training on demand
- **Model Info**: See latest model ID, sample count, and training timestamp
- **Confidence Settings**: Adjust runtime decision thresholds

### Bridge Monitoring
- **Host Bridge Status**: Real-time capture and input bridge health
- **Frame Resolution**: Monitor actual game resolution for capture validation
- **Action Execution**: See recent actions sent to the game in real-time

### Recent Actions Log
- **Live Feed**: See actions as they execute (navigate, harvest, interact)
- **Reward + Step**: Track proxy reward and step progression per signal
- **Prompt Visibility**: Shows whether gather prompt was detected for that step (`Prompt: yes/no`)

### Settings
- **Policy Confidence Threshold**: Adjust from 0.0 to 1.0
- **Toggle Controls**: Enable/disable runtime policy and input execution
- **Auto-retrain**: Configure continuous model training

## Why Web Dashboard?

✅ **No Focus Stealing**: Browser tabs don't steal focus from GW2  
✅ **Network Accessible**: Control bot from any device on your network  
✅ **Real-time Updates**: Live status and signal monitoring every 2 seconds  
✅ **Modern UI**: Responsive design works on desktop, tablet, mobile  
✅ **No Terminal Required**: Everything through intuitive web interface  

## API Endpoints Used

The dashboard leverages these existing API endpoints:

- `GET /health` – Bridge status
- `GET /v1/run/status` – Run status
- `POST /v1/run/start` – Start run
- `POST /v1/run/pause` / `/resume` – Pause/resume
- `POST /v1/run/stop` – Stop run
- `POST /v1/training/policy/train` – Train policy
- `GET /v1/training/policy/versions` – Model versions
- `GET /v1/telemetry/recent-signals` – Action log

Plus new dashboard endpoints for telemetry streaming.

## Example Usage

1. **Open Dashboard**:
   ```
   http://localhost:8000
   ```

2. **Click "Start"** to begin autonomous operation

3. **Monitor in Browser**: Watch run status, recent actions, and model info update in real-time

4. **Adjust Settings**: Change confidence threshold or toggle features without restarting

5. **Background Monitoring**: Tab can stay in background while you play GW2

## Settings Persistence

⚠️ **Note**: Settings shown in the dashboard are display-only. To persistently change bot behavior, update your `.env` file:

```bash
GW2_RUNTIME_POLICY_ENABLED=true
GW2_RUNTIME_INPUT_ENABLED=true
GW2_TRAINING_AUTO_RETRAIN_ENABLED=true
GW2_RUNTIME_POLICY_MIN_CONFIDENCE=0.7
```

Then restart the bot.
