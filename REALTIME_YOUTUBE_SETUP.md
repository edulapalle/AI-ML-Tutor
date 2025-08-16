# Real-Time YouTube Pipeline Setup Guide

## 🎯 **Overview**

Set up automatic detection and processing of new StatQuest videos using two approaches:

1. **📊 Polling Monitor** - Checks every 30 minutes using YouTube Data API
2. **⚡ Webhook Server** - Gets instant notifications via YouTube webhooks

## 📋 **Prerequisites**

### Required API Keys & Services

```bash
# Add to your .env file
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
WEBHOOK_CALLBACK_URL=https://your-domain.com/youtube-webhook  # For webhooks
WEBHOOK_VERIFY_TOKEN=your-random-secret-token                 # For webhooks

# Existing keys (already have these)
OPENAI_API_KEY=...
MILVUS_URI=...
MILVUS_TOKEN=...
NEO4J_URI=...
NEO4J_PASSWORD=...
```

### Get YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Create credentials → API Key
5. Copy the API key to your `.env` file

## 🔄 **Option 1: Polling Monitor (Recommended for Start)**

### Features
- ✅ Simple to set up and run
- ✅ No external dependencies
- ✅ Works behind firewalls
- ⏰ Checks every 30 minutes (configurable)
- 📊 Uses YouTube Data API quotas efficiently

### Setup & Usage

```bash
# Install additional dependencies
pip install requests

# Test the monitor (dry run)
python youtube_realtime_monitor.py --test

# Start continuous monitoring (30 min intervals)
python youtube_realtime_monitor.py

# Custom interval (check every 15 minutes)
python youtube_realtime_monitor.py --interval 15
```

### Run as Service (Linux/Mac)

```bash
# Create systemd service
sudo nano /etc/systemd/system/youtube-monitor.service
```

```ini
[Unit]
Description=YouTube Real-Time Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/your/project
Environment=PATH=/path/to/your/venv/bin
ExecStart=/path/to/your/venv/bin/python youtube_realtime_monitor.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable youtube-monitor
sudo systemctl start youtube-monitor
sudo systemctl status youtube-monitor
```

## ⚡ **Option 2: Webhook Server (For Real-Time)**

### Features
- ⚡ Instant notifications (0-5 second delay)
- 🚀 No polling overhead
- 📡 YouTube pushes notifications to your server
- 🔄 More complex setup but more efficient

### Setup & Usage

```bash
# Install additional dependencies
pip install aiohttp

# For local testing, install ngrok
# Download from: https://ngrok.com/

# Start ngrok tunnel (in separate terminal)
ngrok http 8080

# Copy the ngrok HTTPS URL to your .env
# WEBHOOK_CALLBACK_URL=https://abc123.ngrok.io/youtube-webhook

# Start webhook server
python youtube_webhook_server.py --port 8080

# Subscribe to StatQuest notifications
curl -X POST http://localhost:8080/subscribe

# Check server health
curl http://localhost:8080/health
```

### Production Deployment

For production, deploy to a cloud service with a permanent URL:

```bash
# Example: Deploy to Railway, Heroku, or DigitalOcean
# Set environment variables:
WEBHOOK_CALLBACK_URL=https://your-app.railway.app/youtube-webhook
WEBHOOK_VERIFY_TOKEN=super-secret-random-token-here
```

## 🔧 **Integration with Existing Code**

Both scripts are designed to integrate with your existing processing pipeline:

### Required Integrations

1. **Transcript Extraction**: Connect to your existing `youtube-transcript-api` code
2. **Milvus Loading**: Connect to your existing Milvus insertion functions  
3. **Neo4j Loading**: Connect to your existing Neo4j knowledge graph code

### Integration Points

```python
# In youtube_realtime_monitor.py or youtube_webhook_server.py

async def load_to_milvus(self, video: VideoInfo) -> bool:
    """Replace this with your existing Milvus code"""
    # Import your existing functions
    from load_rich_concepts_to_milvus_new import process_video_content
    
    success = await process_video_content(video.video_id, video.title)
    return success

async def load_to_neo4j(self, video: VideoInfo) -> bool:
    """Replace this with your existing Neo4j code"""
    # Import your existing functions  
    from build_kg import add_video_to_knowledge_graph
    
    success = await add_video_to_knowledge_graph(video)
    return success
```

## 📊 **Monitoring & Logs**

### View Logs

```bash
# Polling monitor logs
tail -f youtube_monitor.log

# Webhook server logs (if using systemd)
sudo journalctl -u youtube-webhook -f

# Check processed videos
cat processed_videos.json
```

### Log Output Examples

```
2025-08-15 14:30:00 - INFO - 🆕 New video detected: Machine Learning Explained Simply
2025-08-15 14:30:05 - INFO - 📝 Transcript extracted: 15,423 characters
2025-08-15 14:30:12 - INFO - 🔍 Loading to Milvus...
2025-08-15 14:30:18 - INFO - ✅ Milvus loading completed
2025-08-15 14:30:19 - INFO - 🕸️ Loading to Neo4j...
2025-08-15 14:30:23 - INFO - ✅ Neo4j loading completed
2025-08-15 14:30:24 - INFO - 🎉 Successfully processed: Machine Learning Explained Simply
```

## ⚠️ **Important Notes**

### API Quotas
- YouTube Data API has daily quotas (10,000 units/day free)
- Each video search uses ~5 units
- Each video details request uses ~1 unit
- Monitor usage in Google Cloud Console

### Data Safety
- Both approaches check for already-processed videos
- No existing data is deleted
- Failed processing attempts are logged and retried

### Error Handling
- Automatic retry on temporary failures
- Graceful handling of API rate limits
- Detailed logging for debugging

## 🚀 **Quick Start (Recommended)**

1. **Get YouTube API key** (see above)
2. **Add to .env file**:
   ```bash
   YOUTUBE_API_KEY=your_api_key_here
   ```
3. **Test the polling monitor**:
   ```bash
   python youtube_realtime_monitor.py --test
   ```
4. **If test works, start monitoring**:
   ```bash
   python youtube_realtime_monitor.py
   ```

That's it! Your system will now automatically detect and process new StatQuest videos every 30 minutes.

## 🤝 **Support**

If you encounter issues:
1. Check the logs for error messages
2. Verify API keys are correct
3. Ensure existing Milvus/Neo4j functions work
4. Test with a known recent video first

The system is designed to be resilient and will continue monitoring even if individual video processing fails.
