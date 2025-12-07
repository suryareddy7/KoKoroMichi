## Deployment Guide for KoKoroMichi

This guide covers deploying KoKoroMichi to various hosting platforms.

### Prerequisites

- Python 3.10+
- discord.py (v2.x)
- Discord bot token from [Discord Developer Portal](https://discord.com/developers)
- (Optional) MongoDB or PostgreSQL for remote data storage

---

## Local Development

### Quick Start

1. **Clone the repository and install dependencies:**
   ```bash
   git clone <repo-url>
   cd KoKoroMichi
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your DISCORD_TOKEN
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

### Docker Development

Using Docker Compose for local development with optional MongoDB/PostgreSQL:

```bash
# Start bot with local JSON storage
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

---

## Production Deployment

### Render.com

1. **Create a New Web Service**
   - Select `Docker` environment
   - Connect your GitHub repository
   - Set root directory (if needed)

2. **Add Environment Variables:**
   - `DISCORD_TOKEN` — Your Discord bot token
   - `PROVIDER` — `local` or `mongo`
   - `LOG_LEVEL` — `INFO` or `DEBUG`
   - `MONGO_URI` — If using MongoDB adapter

3. **Deploy:**
   - Render will auto-deploy on push to main

### Railway.app

1. **Connect GitHub Repository**
2. **Add Environment Variables:**
   - `DISCORD_TOKEN`
   - `PROVIDER`
   - `LOG_LEVEL`
   - Optional: `MONGO_URI`, `DATABASE_URL`

3. **Add MongoDB or PostgreSQL Service:**
   - Add from Railway's service marketplace
   - Link to bot service

### Heroku (via GitHub Actions)

Provided in `.github/workflows/heroku-deploy.yml` (auto-deploy on release tag).

### Self-Hosted (VPS)

1. **SSH into your VPS**
2. **Install Python 3.10+ and Git**
3. **Clone and setup:**
   ```bash
   git clone <repo-url>
   cd KoKoroMichi
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run with systemd (recommended):**
   Create `/etc/systemd/system/kokoromichi.service`:
   ```ini
   [Unit]
   Description=KoKoroMichi Discord Bot
   After=network.target

   [Service]
   Type=simple
   User=nobody
   WorkingDirectory=/home/user/KoKoroMichi
   ExecStart=/home/user/KoKoroMichi/.venv/bin/python bot.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/home/user/KoKoroMichi/.env

   [Install]
   WantedBy=multi-user.target
   ```

   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable kokoromichi
   sudo systemctl start kokoromichi
   sudo systemctl status kokoromichi
   ```

---

## Data Storage Options

### Local JSON (Default)

- **Setup:** None, uses built-in `data/` directory
- **Best for:** Development, small deployments
- **Persistence:** Files backed up automatically

### MongoDB (Remote)

1. **Create MongoDB Atlas cluster** (free tier available)
2. **Set environment variables:**
   ```bash
   PROVIDER=mongo
   MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/kokoromichi
   ```

### PostgreSQL (Remote)

1. **Create Postgres database** (e.g., on AWS RDS, Render, Railway)
2. **Set environment variables:**
   ```bash
   PROVIDER=postgres
   DATABASE_URL=postgresql://user:pass@host:5432/kokoromichi
   ```

---

## Monitoring and Debugging

### Logs

Set `LOG_LEVEL` environment variable:
- `DEBUG` — Verbose logging
- `INFO` — Standard logging (default)
- `WARNING` — Only warnings and errors
- `ERROR` — Only errors

### Health Checks

The bot logs on startup:
```
✓ Loaded cog: profile
✓ Loaded cog: economy
...
Logged in as BotName (ID: 123456789)
Connected to 5 guilds
Data provider initialized: LocalJSONProvider
```

---

## Scaling Considerations

1. **Single-Server Setup** — Use local JSON provider; works well up to ~10k users
2. **Multi-Server Setup** — Migrate to MongoDB or PostgreSQL
3. **Caching** — LocalJSONProvider includes TTL cache; adjust debounce_seconds in provider_manager.py
4. **Rate Limiting** — Built into discord.py

---

## Troubleshooting

### "DISCORD_TOKEN not set"
- Ensure `.env` file exists and has `DISCORD_TOKEN=<your-token>`
- On Render/Railway, verify env var in dashboard

### "Connection refused" (database)
- Verify MongoDB/PostgreSQL service is running
- Check connection string in `.env`
- For Docker: ensure services are on same network

### Bot doesn't respond to commands
- Check bot has message content intent enabled (should be in bot.py)
- Verify bot has necessary Discord permissions in guild
- Check logs: `LOG_LEVEL=DEBUG python bot.py`

---

## Backup and Recovery

### JSON Files
Automatic backups created in `data/backups/` before each write. Keep these on a separate storage (e.g., S3, cloud storage).

### Database Backups
- **MongoDB Atlas:** Automatic snapshots
- **PostgreSQL:** Use pg_dump regularly
- **Automated:** Set up cron jobs or cloud provider backups

---

## Performance Tips

1. **Cache TTL:** Increase `cache_ttl` in LocalJSONProvider for higher load
2. **Debounce:** Adjust `debounce_seconds` to batch writes (trade-off: eventual consistency)
3. **Database:** Use PostgreSQL over local JSON for >10k users
4. **Monitoring:** Track command latency with logging

---

## Support

- **Issues:** Open an issue on GitHub
- **Discussions:** Check repo discussions
- **Logs:** Always provide logs when reporting issues
