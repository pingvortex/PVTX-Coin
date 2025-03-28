# PVTX Coin System

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)

A proof-of-work cryptocurrency system with Flask-based server and lightweight mining client.

## System Architecture
- **Server**: Flask API (server.py) with SQLite database
- **Client**: Python CLI miner (pvtxcoinminer.py)
- **Consensus**: Proof-of-Work with dynamic reward calculation
- **Cryptography**: Password hashing with Werkzeug security

## Features ✨
- 🖥️ REST API server with JWT-like authentication
- ⛏️ CPU-based mining algorithm with decreasing rewards
- 👤 User registration/login system
- 💰 Wallet system with coin transfers
- 📜 Transaction history tracking
- ⚖️ Balance management with SQL transactions
- 📊 Automatic database schema initialization

## Prerequisites 📋
- Python 3.7+
- pip package manager
- SQLite3 (included with Python)

## Installation ⚡

### 1. Clone Repository
```bash
git clone https://github.com/PingVortex/PVTX-Coin.git
cd PVTX-Coin
```

### 2. Install Dependencies
**Server Requirements:**
```bash
pip install flask python-dotenv werkzeug
```

**Client Requirements:**
```bash
pip install requests
```

## Server Setup 🖥️

### 1. Configure Environment
Create `.env` file:
```env
SECRET_KEY=your_secure_key_here
```

### 2. Initialize Database
```bash
python3 server.py
```
(This automatically creates pvtxc.db on first run)

### 3. Start Server
```bash
python3 server.py
```
Server runs on `0.0.0.0:5057` by default

## Client Configuration ⚙️

### 1. Set Server URL
In `pvtxcoinminer.py`:
```python
SERVER_URL = "http://localhost:5057"  # For local development
```

### 2. Run Miner Client
```bash
python3 pvtxcoinminer.py
```

## Development Setup 🔧

### Local Testing
1. Start server in terminal 1:
```bash
python3 server.py
```

2. Start miner in terminal 2:
```bash
python3 pvtxcoinminer.py
```

3. Open second miner instance to test transfers

### Production Deployment
1. Set proper WSGI server (Gunicorn/UWSGI)
2. Configure reverse proxy (Nginx/Apache)
3. Set production SECRET_KEY
4. Enable HTTPS
5. Regular database backups

## API Endpoints 🔗
| Endpoint       | Method | Description                |
|----------------|--------|----------------------------|
| /register      | POST   | User registration          |
| /login         | POST   | User authentication        |
| /mine          | POST   | Submit mining solution     |
| /transfer      | POST   | Transfer coins             |
| /transactions  | POST   | Get transaction history    |
| /problem       | POST   | Get mining problem         |

## Security Considerations 🔒
- Uses Werkzeug password hashing
- SQL injection protected through parameterized queries
- Sensitive credentials never stored in plaintext
- Production requires:
  - HTTPS encryption
  - Rate limiting
  - Input validation
  - Regular security audits

## Troubleshooting 🐞
**Server not starting:**
- Check port 5057 availability
- Verify database file permissions
- Check .env file exists

**Mining errors:**
- Verify client and server versions match
- Check system clock synchronization
- Ensure client points to correct server URL

**Transaction issues:**
- Confirm recipient username exists
- Verify sufficient balance
- Check transaction history for errors

## Contributing 🤝
Contributions are welcome! Please:

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## License 📄
Distributed under MIT License. See `LICENSE` for details.

## Disclaimer ⚠️
This is an **educational project** demonstrating basic cryptocurrency concepts. Not suitable for:
- Real financial transactions
- Production environments
- Investment purposes

## Community 💬
Join development discussions:
[![Discord](https://img.shields.io/badge/Discord-Join-7289DA?logo=discord)](https://discord.gg/At3CcCqcR2)
