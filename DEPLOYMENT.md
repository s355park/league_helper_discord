# Deployment Guide - 24/7 Hosting Options

This guide covers the cheapest ways to host your Discord bot 24/7.

## Option 1: Render (FREE - Recommended for Starting)

**Cost:** FREE (750 hours/month, spins down after 15 min inactivity)

### Setup Steps:

1. **Create Render Account**
   - Go to [render.com](https://render.com) and sign up (free)

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Or use "Public Git Repository" and paste your repo URL

3. **Configure Service**
   - **Name:** `league-discord-bot`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 start.py`
   - **Plan:** Free

4. **Add Environment Variables**
   - Go to "Environment" tab
   - Add these variables:
     ```
     DISCORD_BOT_TOKEN=your_token_here
     RIOT_API_KEY=your_key_here
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     DEFAULT_REGION=na1
     PORT=8000
     API_HOST=0.0.0.0
     API_PORT=8000
     ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

**Note:** Free tier spins down after 15 min of inactivity. Your bot will wake up when someone uses a command, but there's a ~30 second delay on first request.

---

## Option 2: Railway ($5/month - Most Reliable)

**Cost:** $5/month credit, then pay-as-you-go (~$0.50-2/month for a small bot)

### Setup Steps:

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app) and sign up
   - Get $5 free credit to start

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or upload code)

3. **Configure Service**
   - Railway auto-detects Python
   - It will use `railway.json` for configuration
   - Start command: `bash start.sh`

4. **Add Environment Variables**
   - Go to "Variables" tab
   - Add all the same variables as Render (see above)

5. **Deploy**
   - Railway auto-deploys on push
   - Check logs to ensure both services start

**Advantages:** No spin-down, always-on, very reliable

---

## Option 3: Fly.io (FREE - Good Alternative)

**Cost:** FREE (3 shared-cpu VMs, 3GB storage)

### Setup Steps:

1. **Install Fly CLI**
   ```bash
   # Windows (PowerShell)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Create Fly App**
   ```bash
   fly auth login
   fly launch
   ```

3. **Configure `fly.toml`** (created automatically)
   - Set build and start commands
   - Configure environment variables

4. **Deploy**
   ```bash
   fly deploy
   ```

---

## Option 4: Vultr VPS ($2.50-6/month - Full Control)

**Cost:** $2.50-6/month (cheapest reliable VPS)

### Setup Steps:

1. **Create Vultr Account**
   - Go to [vultr.com](https://vultr.com)
   - Sign up and add payment method

2. **Create Server**
   - Click "Deploy Server"
   - **Server Type:** Cloud Compute
   - **CPU & Storage:** Regular Performance ($6/month) or Shared vCPU ($2.50/month)
   - **Location:** Choose closest to you
   - **OS:** Ubuntu 22.04
   - **SSH Key:** Add your SSH key (recommended)

3. **SSH into Server**
   ```bash
   ssh root@your_server_ip
   ```

4. **Install Dependencies**
   ```bash
   # Update system
   apt update && apt upgrade -y
   
   # Install Python and pip
   apt install python3 python3-pip git -y
   
   # Install Python dependencies
   pip3 install -r requirements.txt
   ```

5. **Set Up Environment Variables**
   ```bash
   # Create .env file
   nano .env
   # Paste all your environment variables
   ```

6. **Set Up Systemd Service (Auto-start on boot)**
   ```bash
   # Create service file
   sudo nano /etc/systemd/system/league-bot.service
   ```
   
   Paste this:
   ```ini
   [Unit]
   Description=League Discord Bot
   After=network.target
   
   [Service]
   Type=simple
   User=root
   WorkingDirectory=/root/league_helper_discord
   Environment="PATH=/usr/bin:/usr/local/bin"
   ExecStart=/usr/bin/python3 /root/league_helper_discord/start.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

7. **Enable and Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable league-bot
   sudo systemctl start league-bot
   sudo systemctl status league-bot
   ```

---

## Option 5: DigitalOcean App Platform ($5/month)

Similar to Railway but with DigitalOcean's infrastructure.

1. Go to [digitalocean.com](https://digitalocean.com)
2. Create App Platform service
3. Connect GitHub repo
4. Configure environment variables
5. Deploy

---

## Recommended: Start with Render (Free)

**Best path:**
1. Start with **Render FREE** to test
2. If you need always-on (no spin-down), switch to **Railway** ($5/month credit)
3. For full control, use **Vultr** ($2.50-6/month)

---

## Making Your Bot Always-On (Prevent Spin-Down)

If using Render free tier, you can keep it awake with a simple ping:

1. Create a free [UptimeRobot](https://uptimerobot.com) account
2. Add a monitor for your Render URL: `https://your-app.onrender.com/health`
3. Set it to ping every 5 minutes
4. This keeps your bot awake 24/7 (stays within free tier limits)

**Alternative:** Use [cron-job.org](https://cron-job.org) (free) to ping your health endpoint every 5 minutes.

---

## Troubleshooting

### Bot goes offline
- Check service logs in your hosting dashboard
- Verify environment variables are set correctly
- Ensure both FastAPI and bot processes are running

### High memory usage
- Discord bots typically use 50-200MB RAM
- Free tiers usually have 512MB-1GB limit
- If you hit limits, upgrade to paid tier

### Port issues
- Render/Railway auto-assign PORT variable
- Use `PORT` environment variable in your code
- FastAPI should bind to `0.0.0.0` and use `PORT`

---

## Cost Comparison Summary

| Service | Cost | Always-On | Best For |
|---------|------|-----------|----------|
| Render Free | $0 | No (spins down) | Testing, low traffic |
| Railway | $5/mo credit | Yes | Production, reliability |
| Fly.io | $0 | Yes | Production, free tier |
| Vultr | $2.50-6/mo | Yes | Full control, custom setup |
| DigitalOcean | $5/mo | Yes | Production, DO ecosystem |

**My Recommendation:** Start with **Render Free** → Upgrade to **Railway** if you need always-on.

