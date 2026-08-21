# GCP Migration & Deployment Guide

This guide provides a step-by-step walkthrough to deploy **`codeflip.co.in`** (`coderacer-web`) and **`conacy.codeflip.co.in`** (`conacy-web`) onto a **single GCP Compute Engine VM instance** to minimize hosting costs while preserving your existing AWS configuration files as fallback.

---

## 🏗️ Architectural Overview

```
                        +--------------------------------+
                        |  Cloudflare DNS & SSL Edge     |
                        |  (codeflip.co.in & subdomains) |
                        +---------------+----------------+
                                        |
                            HTTPS / HTTP Traffic
                                        v
                       +---------------------------------+
                       |  GCP Compute Engine (Static IP) |
                       |  Host OS (Ubuntu 24.04 LTS)     |
                       |  Swap: 4GB                      |
                       +----------------+----------------+
                                        |
                        +---------------+---------------+
                        | Main Nginx Gateway (Port 80)  |
                        +-------+---------------+-------+
                                |               |
          Host Header:          |               | Host Header:
          codeflip.co.in        |               | conacy.codeflip.co.in
          www.codeflip.co.in    v               v
                +-------------------+   +-------------------+
                |  coderacer-web    |   |    conacy-web     |
                |  (Docker Stack)   |   |   (Docker Stack)  |
                |  - Next.js (web)  |   |  - Vite Client    |
                |  - Django (api)   |   |  - Express Server |
                |  - Postgres       |   |  - Neo4j          |
                |  - Redis          |   |  - Redis          |
                +-------------------+   +-------------------+
```

---

## 📋 Step 1: Create and Configure GCP Compute Engine VM

### 1.1 Create the VM Instance
1. Log into **[Google Cloud Console](https://console.cloud.google.com/)**.
2. Navigate to **Compute Engine > VM instances** and click **Create Instance**.
3. Configure the VM parameters:
   - **Name**: `codeflip-production-vm`
   - **Region**: Choose a region close to your target users (e.g., `asia-south1` Mumbai, `us-central1` Iowa, or `europe-west1` Belgium).
   - **Machine Configuration**:
     - **Series**: `E2`
     - **Machine type options (Maximized for $300 free credits over 87 days)**:
       - 🚀 **`e2-standard-4` (4 vCPU, 16 GB RAM)**: **Recommended Top Pick!** Costs ~$97/month (~$280 total for 87 days). Fits 100% within your $300 credit limit with ₹0 out-of-pocket cost. Next.js builds & Neo4j DB run ultra-fast!
       - ⚡ **`e2-standard-2` (2 vCPU, 8 GB RAM)**: Costs ~$50/month (~$145 total for 87 days). Uses only 50% of your credits, leaving a huge safety buffer.
       - 💾 **`e2-highmem-2` (2 vCPU, 16 GB RAM)**: Costs ~$82/month (~$240 total for 87 days). Ideal if memory is your main bottleneck.
   - **Boot Disk**:
     - Operating System: **Ubuntu**
     - Version: **Ubuntu 24.04 LTS**
     - Boot disk type: **Balanced persistent disk** (30 GB - 50 GB capacity recommended).
   - **Firewall**:
     - Check **Allow HTTP traffic**
     - Check **Allow HTTPS traffic**

### 1.2 Reserve a Static External IP Address
1. In GCP Console, go to **VPC Network > IP addresses**.
2. Click **Reserve External Static IP Address**.
3. Name: `codeflip-static-ip`.
4. Attach it to your VM instance `codeflip-production-vm`.
5. Note down the allocated IPv4 address (e.g., `34.xxx.xxx.xxx`).

### 1.3 Configure GCP Firewall Rules
Ensure ports 22 (SSH), 80 (HTTP), and 443 (HTTPS) are open:
1. Go to **VPC Network > Firewall**.
2. Confirm default rules allow `tcp:80` and `tcp:443` for targets marked `http-server` and `https-server`.

---

## 🛠️ Step 2: Server Initialization & RAM Optimization

Connect to your GCP instance via SSH (using `gcloud compute ssh codeflip-production-vm` or the Cloud Console SSH button).

### 2.1 Install Docker & Docker Compose (Official Docker Repository)
Run the official Docker convenience script which installs `docker-ce`, `docker-ce-cli`, and `docker-compose-plugin` cleanly on Ubuntu:

```bash
# Download and run official Docker installer
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Apply group permissions to current session
exec sg docker -c "$SHELL"

# Verify installation
docker --version
docker compose version
```

### 2.2 Configure 4GB Swap Space (Crucial for Low-Resource VMs)
Running Django + Next.js + Postgres + Express + Neo4j + Redis on a single VM can exceed 2-4GB RAM during builds or high load. Swap prevents OOM crashes:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap persistent across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Tune swappiness
sudo sysctl vm.swappiness=20
echo 'vm.swappiness=20' | sudo tee -a /etc/sysctl.conf
```

---

## 🌐 Step 3: Cloudflare DNS & SSL Configuration

Since Cloudflare manages your nameservers, you can manage both domains (`codeflip.co.in` and `conacy.codeflip.co.in`) with free Edge SSL and DDoS protection.

### 3.1 Update Cloudflare DNS Records
In your **Cloudflare Dashboard** under `codeflip.co.in` -> **DNS > Records**:

| Type | Name | Content / Target | Proxy status |
| :--- | :--- | :--- | :--- |
| **A** | `@` | `<YOUR_GCP_STATIC_IP>` | Proxied (Orange Cloud) |
| **A** | `www` | `<YOUR_GCP_STATIC_IP>` | Proxied (Orange Cloud) |
| **A** | `conacy` | `<YOUR_GCP_STATIC_IP>` | Proxied (Orange Cloud) |

### 3.2 Configure SSL/TLS Mode
1. Go to **SSL/TLS > Overview** in Cloudflare.
2. Set SSL/TLS encryption mode to **Flexible** (Cloudflare handles HTTPS to users, HTTP to GCP VM) OR **Full** (Cloudflare connects to GCP VM over HTTP/HTTPS).

---

## 🔀 Step 4: Multi-Site Reverse Proxy Setup on GCP

To run both `coderacer-web` and `conacy-web` on the same GCP server without editing their existing AWS compose files, set up a central Nginx Gateway.

### 4.1 Create Gateway Directory Structure
```bash
mkdir -p ~/gateway/conf.d
cd ~/gateway
```

### 4.2 Create Master Nginx Gateway Configuration (`~/gateway/conf.d/gateway.conf`)
Run this command in your VM terminal to create `gateway.conf`:

```bash
cat << 'EOF' > ~/gateway/conf.d/gateway.conf
# Log format
log_format gateway_fmt '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer"';

# --- 1. Main Site: codeflip.co.in & www.codeflip.co.in ---
server {
    listen 80;
    server_name codeflip.co.in www.codeflip.co.in;

    client_max_body_size 100M;
    access_log /var/log/nginx/codeflip.access.log gateway_fmt;

    location / {
        proxy_pass http://127.0.0.1:8081; # Points to coderacer-web Nginx
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# --- 2. Subdomain: conacy.codeflip.co.in ---
server {
    listen 80;
    server_name conacy.codeflip.co.in;

    client_max_body_size 50M;
    access_log /var/log/nginx/conacy.access.log gateway_fmt;

    location / {
        proxy_pass http://127.0.0.1:8082; # Points to conacy-web Nginx
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
```

### 4.3 Create Docker Compose for Gateway (`~/gateway/docker-compose.yaml`)
Run this command in your VM terminal to create `docker-compose.yaml`:

```bash
cat << 'EOF' > ~/gateway/docker-compose.yaml
services:
  gateway:
    image: nginx:alpine
    container_name: main-gateway-nginx
    restart: always
    network_mode: "host" # Uses host network to directly reach localhost:8081 & 8082
    volumes:
      - ./conf.d:/etc/nginx/conf.d:ro
EOF
```

Launch the gateway:
```bash
cd ~/gateway && docker compose up -d
```

---

## 🚀 Step 5: Deploy Projects on GCP Instance

### 5.1 Project 1: `coderacer-web` Setup

Clone project into `~/coderacer-web`:
```bash
cd ~
git clone <YOUR_GIT_REPO_URL_FOR_CODERACER> coderacer-web
cd ~/coderacer-web
```

Create a GCP compose override file `docker-compose.override.yaml` so host ports do not collide (the `!reset` tag clears the default `80:80` binding without touching original `docker-compose.yaml`):

```yaml
services:
  nginx:
    ports: !reset
      - "127.0.0.1:8081:80"
```

Configure `.env` and `./api/.env` / `./web/.env`:
- Ensure database passwords, secret keys, and `NEXT_PUBLIC_BASE_URL=https://www.codeflip.co.in` are set correctly.

Deploy using the low-resource script:
```bash
chmod +x ./scripts/optimize-deploy.sh
./scripts/optimize-deploy.sh
```

---

### 5.2 Project 2: `conacy-web` Setup

Clone project into `~/conacy-web`:
```bash
cd ~
git clone <YOUR_GIT_REPO_URL_FOR_CONACY> conacy-web
cd ~/conacy-web
```

Create GCP compose override file `docker-compose.override.yaml` (or `compose.override.yaml`):
```yaml
services:
  neo4j:
    environment:
      - NEO4J_dbms_memory_heap_initial__size=256m
      - NEO4J_dbms_memory_heap_max__size=512m
      - NEO4J_dbms_memory_pagecache_size=256m

  nginx:
    ports: !reset
      - "127.0.0.1:8082:80"
```

Configure `.env`:
- Set `CLIENT_URL=https://conacy.codeflip.co.in`
- Set `VITE_SERVER_URL=https://conacy.codeflip.co.in`
- Configure Neo4j and Redis credentials.

Deploy `conacy-web`:
```bash
docker compose up -d --build
```

---

## 🔒 Step 6: AWS Fallback & Cost Optimization

To eliminate AWS costs while keeping AWS configs fully intact:

1. **Pause AWS EC2 Instance**:
   - Go to AWS Console > EC2 > Instances.
   - Select your EC2 instance and choose **Instance state > Stop instance**.
   - Do NOT terminate it. You can restart it anytime if needed.

2. **Disable CloudFront Distributions**:
   - Go to AWS CloudFront Console.
   - Select distributions for `codeflip.co.in` and `conacy.codeflip.co.in`.
   - Click **Disable**. Keep them disabled so AWS doesn't bill for requests.

3. **ACM (AWS Certificate Manager)**:
   - ACM certificates are free on AWS. Leave them active in ACM.

---

## ⏰ Step 7: Free Credits Strategy & Automatic Shutdown on Expiration

### 7.1 Free Credits Budgeting (₹28,321 / $300 Credits)
Your trial credit gives you **₹28,321 ($300 USD)** valid until **October 28, 2026** (~87 days / 2.9 months).
This gives you a maximum budget rate of **~$103 USD / month (~₹8,700 / month)**.

#### VM Sizing Options & 87-Day Total Cost:
1. 🚀 **`e2-standard-4` (4 vCPU, 16 GB RAM)**:
   - Monthly cost: ~$97 / month (~₹8,200 / month).
   - **87-Day Total**: **~$280 (~₹23,600)**.
   - **Status**: **100% Covered by Free Credits** (Leaves ~$20 cushion). Runs both apps at lightning speed with zero swap needed!
2. ⚡ **`e2-standard-2` (2 vCPU, 8 GB RAM)**:
   - Monthly cost: ~$50 / month (~₹4,200 / month).
   - **87-Day Total**: **~$145 (~₹12,200)**.
   - **Status**: **100% Covered** (Uses only ~48% of credits, large safety margin).
3. 💾 **`e2-highmem-2` (2 vCPU, 16 GB RAM)**:
   - Monthly cost: ~$82 / month (~₹6,900 / month).
   - **87-Day Total**: **~$238 (~₹20,000)**.
   - **Status**: **100% Covered** (Leaves ~$62 cushion). Perfect for Neo4j graph database heap memory.

---

### 7.2 Automatic Instance Shutdown Setup (3 Safety Layers)

To guarantee you are **never charged a single rupee** after October 28, 2026, implement these 3 failsafe mechanisms:

#### Layer 1: In-VM Scheduled Hard Shutdown (Easiest & Most Reliable)
Install `cron` (if missing) and set a root cron job to shut down the server automatically on October 28, 2026:

```bash
# Install cron if not already installed
sudo apt update && sudo apt install -y cron

# Add cron job to shut down the VM at 00:00 on October 28, 2026
(sudo crontab -l 2>/dev/null; echo "0 0 28 10 * /sbin/shutdown -h now") | sudo crontab -

# Verify cron job
sudo crontab -l
```
*Note: A stopped VM only incurs minimal disk storage fees (~$1/month), but CPU/RAM usage fees immediately drop to $0.*

#### Layer 2: GCP Billing Budget Cap & Email Alerts
1. Open **[GCP Billing Console](https://console.cloud.google.com/billing)**.
2. Click **Budgets & alerts** in the left menu.
3. Click **Create Budget**:
   - **Name**: `Free Credit Expiration Safety`
   - **Amount Type**: Specified amount -> Set to **₹100** (or $1).
   - **Alert Thresholds**: Set alerts at 50%, 90%, and 100%.
   - **Check**: Send notifications to billing admins.

#### Layer 3: Delete / Stop VM via GCP CLI (When Expiration Approaches)
If you do not plan to continue hosting on GCP after October 28:
```bash
# Run this from your local computer or Cloud Shell to permanently delete the VM and static IP:
gcloud compute instances delete codeflip-production-vm --zone=asia-south1-a
gcloud compute addresses delete codeflip-static-ip --region=asia-south1
```

---

## ⚡ Verification Checklist

- [ ] Check `codeflip.co.in` loads main CodeRacer site via GCP.
- [ ] Check `www.codeflip.co.in` redirects / loads correctly.
- [ ] Check `conacy.codeflip.co.in` loads Conacy app via GCP.
- [ ] Confirm both sites have valid SSL certificate badge in browser (issued by Cloudflare).
- [ ] Check memory usage on GCP VM: `free -h` and `docker stats`.
- [ ] Verify automatic shutdown cron job is scheduled: `sudo crontab -l`.
