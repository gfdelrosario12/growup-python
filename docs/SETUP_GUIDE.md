# GrowUp IoT System - Setup Guide

## 📋 Prerequisites

### Hardware Requirements
- Raspberry Pi 4 (4GB RAM recommended)
- MicroSD Card (32GB+ Class 10)
- All sensors listed in ARCHITECTURE.md
- Stable power supply
- Ethernet or Wi-Fi connection

### Software Requirements
- Raspberry Pi OS (Bullseye or later)
- Python 3.9+
- Java 17+ (for Spring Boot backend)
- PostgreSQL 14+
- Node.js 18+ (for frontend)

---

## 🚀 Installation Steps

### Part 1: Raspberry Pi Setup

#### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
```

#### 1.2 Clone Repository
```bash
cd /home/gladwin/Documents/Personal/Grow\ Up
git clone <your-repo-url> rpi
cd rpi
```

#### 1.3 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 1.4 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Create `requirements.txt` if not exists:**
```txt
Flask==3.0.0
requests==2.31.0
APScheduler==3.10.4
smbus2==0.4.3
RPi.GPIO==0.7.1
influxdb-client==1.38.0
python-dotenv==1.0.0
```

#### 1.5 Enable I2C and 1-Wire
```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
# Navigate to: Interface Options → 1-Wire → Enable
# Reboot
sudo reboot
```

#### 1.6 Verify I2C Devices
```bash
sudo apt install -y i2c-tools
sudo i2cdetect -y 1
# Should show addresses like 0x23 (BH1750), 0x76 (BME280)
```

#### 1.7 Configure API Settings
```bash
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
nano api_config.py
```

**Update with your settings:**
```python
# Backend Configuration
BACKEND_HOST = "http://YOUR_BACKEND_IP:8080"
BACKEND_SENSOR_READINGS = f"{BACKEND_HOST}/api/sensor-readings"

# Flask Server
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

# Intervals
SEND_INTERVAL = 1  # Send to backend every 1 second

# Logging
VERBOSE_LOGGING = True
LOG_SENSOR_READINGS = True
```

#### 1.8 Test Sensor Readings
```bash
python3 -c "from server import read_all_sensors; print(read_all_sensors())"
```

---

### Part 2: Spring Boot Backend Setup

#### 2.1 Install Java
```bash
# On Ubuntu/Debian
sudo apt install -y openjdk-17-jdk

# On macOS
brew install openjdk@17

# Verify installation
java -version
```

#### 2.2 Install PostgreSQL
```bash
# On Ubuntu/Debian
sudo apt install -y postgresql postgresql-contrib

# On macOS
brew install postgresql@14

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### 2.3 Create Database
```bash
sudo -u postgres psql

-- Inside PostgreSQL prompt:
CREATE DATABASE growup_db;
CREATE USER growup_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE growup_db TO growup_user;
\q
```

#### 2.4 Configure Spring Boot
Create/edit `src/main/resources/application.properties`:
```properties
# Database Configuration
spring.datasource.url=jdbc:postgresql://localhost:5432/growup_db
spring.datasource.username=growup_user
spring.datasource.password=your_secure_password
spring.datasource.driver-class-name=org.postgresql.Driver

# JPA Configuration
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=false
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect
spring.jpa.properties.hibernate.format_sql=true

# Server Configuration
server.port=8080

# CORS Configuration (adjust in production)
cors.allowed.origins=http://localhost:3000,http://192.168.1.100:3000

# Logging
logging.level.com.growup.backend=INFO
logging.file.name=logs/spring-boot-application.log
```

#### 2.5 Build Backend
```bash
cd /path/to/spring-boot-project
./mvnw clean install

# Or with Gradle:
./gradlew build
```

#### 2.6 Run Backend
```bash
# Development
./mvnw spring-boot:run

# Production (using JAR)
java -jar target/backend-0.0.1-SNAPSHOT.jar

# As background service
nohup java -jar target/backend-0.0.1-SNAPSHOT.jar > logs/backend.log 2>&1 &
```

#### 2.7 Verify Backend
```bash
# Test health endpoint (if configured)
curl http://localhost:8080/actuator/health

# Test sensor readings endpoint
curl http://localhost:8080/api/sensor-readings/latest
```

---

### Part 3: Frontend Setup (Next.js)

#### 3.1 Install Node.js
```bash
# On Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# On macOS
brew install node@18

# Verify installation
node --version
npm --version
```

#### 3.2 Create Next.js Project (if not exists)
```bash
npx create-next-app@latest growup-frontend
cd growup-frontend
```

#### 3.3 Install Dependencies
```bash
npm install recharts lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### 3.4 Configure Environment Variables
Create `.env.local`:
```bash
NEXT_PUBLIC_RASPI_HOST=http://192.168.1.100:5000
NEXT_PUBLIC_BACKEND_HOST=http://localhost:8080
```

#### 3.5 Create API Proxy Route
Create `app/api/sensors/route.ts`:
```typescript
export async function GET() {
  try {
    const raspiHost = process.env.NEXT_PUBLIC_RASPI_HOST || 'http://localhost:5000'
    const response = await fetch(`${raspiHost}/sensors`, {
      cache: 'no-store',
      headers: {
        'Accept': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    
    const data = await response.json()
    return Response.json(data)
  } catch (error) {
    console.error('❌ Failed to fetch sensor data:', error)
    return Response.json(
      { status: 'error', message: 'Failed to fetch sensor data' },
      { status: 500 }
    )
  }
}
```

#### 3.6 Run Frontend
```bash
# Development mode
npm run dev

# Production build
npm run build
npm start

# Preview build
npm run build && npm run start
```

#### 3.7 Access Frontend
Open browser: `http://localhost:3000/analytics`

---

## 🔧 System Configuration

### Create Systemd Services

#### Raspberry Pi Service
```bash
sudo nano /etc/systemd/system/growup-iot.service
```

**Content:**
```ini
[Unit]
Description=GrowUp IoT System
After=network.target

[Service]
Type=simple
User=gladwin
WorkingDirectory=/home/gladwin/Documents/Personal/Grow Up/rpi
ExecStart=/home/gladwin/Documents/Personal/Grow Up/rpi/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable growup-iot
sudo systemctl start growup-iot
sudo systemctl status growup-iot
```

#### Spring Boot Service
```bash
sudo nano /etc/systemd/system/growup-backend.service
```

**Content:**
```ini
[Unit]
Description=GrowUp Spring Boot Backend
After=postgresql.service

[Service]
Type=simple
User=backend-user
WorkingDirectory=/opt/growup/backend
ExecStart=/usr/bin/java -jar backend.jar
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable growup-backend
sudo systemctl start growup-backend
sudo systemctl status growup-backend
```

---

## 🧪 Testing the System

### 1. Test Raspberry Pi Sensors
```bash
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
source venv/bin/activate
python3 -c "from server import read_all_sensors; import json; print(json.dumps(read_all_sensors(), indent=2))"
```

**Expected output:**
```json
{
  "waterTemp": 23.5,
  "ph": 7.0,
  "dissolvedO2": 8.2,
  "airTemp": 25.0,
  "lightIntensity": 450,
  "waterLevel": 85,
  "waterFlow": 12,
  "humidity": 65,
  "ammonia": 0.02,
  "airPressure": 1013.5
}
```

### 2. Test Flask API
```bash
# In one terminal, start Flask server
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
source venv/bin/activate
python3 server.py

# In another terminal, test the endpoint
curl http://localhost:5000/sensors | jq
```

### 3. Test Backend Connection
```bash
# Test POST (save sensor reading)
curl -X POST http://localhost:8080/api/sensor-readings \
  -H "Content-Type: application/json" \
  -d '{
    "waterTemp": 23.5,
    "phLevel": 7.0,
    "dissolvedO2": 8.2,
    "ammonia": 0.02
  }' | jq

# Test GET (latest reading)
curl http://localhost:8080/api/sensor-readings/latest | jq

# Test GET (last 24 hours)
curl http://localhost:8080/api/sensor-readings/last-24h | jq
```

### 4. Test Complete Data Flow
```bash
# Start all services
cd /home/gladwin/Documents/Personal/Grow\ Up/rpi
source venv/bin/activate
python3 main.py

# In another terminal, monitor logs
tail -f /var/log/growup/main.log

# In a third terminal, watch database
sudo -u postgres psql -d growup_db -c "SELECT COUNT(*) FROM sensor_readings;"
```

### 5. Test Frontend
```bash
# Open browser developer console (F12)
# Navigate to: http://localhost:3000/analytics
# Check Network tab for API calls to /api/sensors
# Verify data is updating every 5 seconds
```

---

## 🔍 Troubleshooting

### Issue: I2C Devices Not Detected
```bash
# Check if I2C is enabled
ls /dev/i2c-*

# Scan for devices
sudo i2cdetect -y 1

# If empty, enable I2C:
sudo raspi-config
# Interface Options → I2C → Enable → Reboot
```

### Issue: Cannot Connect to Backend
```bash
# Check if backend is running
sudo systemctl status growup-backend

# Check backend logs
sudo journalctl -u growup-backend -f

# Test connectivity
curl -v http://localhost:8080/api/sensor-readings/latest

# Check firewall
sudo ufw status
sudo ufw allow 8080/tcp
```

### Issue: Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d growup_db -c "SELECT 1;"

# Check credentials in application.properties
# Verify database exists
sudo -u postgres psql -l | grep growup_db
```

### Issue: Frontend Not Fetching Data
```bash
# Check Raspberry Pi Flask server
curl http://RASPI_IP:5000/sensors

# Check CORS settings in api_config.py
# Verify .env.local has correct IP address

# Check browser console for errors (F12)
```

### Issue: Sensors Returning None
```bash
# Check sensor connections
# Verify power supply is adequate (5V 3A for RPi)

# Test individual sensors:
python3 -c "from sensors.ds18b20 import read_temperature; print(read_temperature())"

# Check for permission issues
sudo usermod -a -G i2c,spi,gpio $USER
# Logout and login again
```

---

## 📊 Verify Installation Checklist

- [ ] Raspberry Pi boots successfully
- [ ] All sensors detected (I2C, 1-Wire, GPIO)
- [ ] Python virtual environment activated
- [ ] Flask server responds on port 5000
- [ ] PostgreSQL database created
- [ ] Spring Boot backend running on port 8080
- [ ] Backend can save sensor readings
- [ ] Frontend accessible on port 3000
- [ ] Frontend fetches data from Raspberry Pi
- [ ] Data flows: Sensors → Backend → Database
- [ ] System logs are being written
- [ ] Services start automatically on boot

---

## 🔐 Security Hardening (Production)

### 1. Change Default Passwords
```bash
# Raspberry Pi user
passwd

# PostgreSQL user
sudo -u postgres psql
ALTER USER growup_user WITH PASSWORD 'new_secure_password';
```

### 2. Enable Firewall
```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 5000/tcp  # Flask API
sudo ufw allow 8080/tcp  # Spring Boot
sudo ufw enable
```

### 3. Disable SSH Password Authentication
```bash
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PubkeyAuthentication yes
sudo systemctl restart sshd
```

### 4. Configure HTTPS (with Let's Encrypt)
```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d your-domain.com
# Update api_config.py to use https://
```

---

## 📝 Next Steps

1. **Configure Alerts**: Set up email/SMS notifications for critical values
2. **Add Monitoring**: Install Grafana for visualization
3. **Schedule Backups**: Automate database backups
4. **Optimize Performance**: Add Redis caching layer
5. **Scale System**: Add more Raspberry Pis for multi-zone monitoring

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Support**: See docs/TROUBLESHOOTING.md for common issues
