#  CESNET Network Anomaly Detection System

> **Real-time network anomaly detection using unsupervised deep learning (Autoencoder PyTorch) on the CESNET-TimeSeries24 dataset, deployed via FastAPI + Docker with a live Streamlit dashboard.**

---

##  Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Results](#results)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Real-Time Pipeline](#real-time-pipeline)
- [Dataset](#dataset)

---

##  Overview

Traditional firewalls only block **known threats**. This system detects **any anomalous behavior** — including zero-day attacks — without requiring labeled data.

### Key Features

-  **Unsupervised Learning** — No labeled attack data needed
-  **Near Real-Time Detection** — Anomalies detected in < 30 seconds
-  **Live Dashboard** — WebSocket-powered real-time visualization
-  **Production Ready** — Fully containerized with Docker
-  **AUC-ROC: 0.96** — Outperforms Isolation Forest baseline (0.86)

---

##  Architecture

```
Virtual Network Lab (Vagrant + VirtualBox)
┌─────────────────────────────────────────┐
│  VM1 (192.168.56.10)                    │
│  tshark captures traffic continuously   │
│         ↓ every 10 seconds              │
│  CSV exported to shared folder          │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Windows Host                           │
│  wireshark_to_cesnet.py                 │
│  Converts raw packets → 12 CESNET       │
│  features (aggregated per minute)       │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Redis Queue                            │
│  Buffers network flows                  │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  FastAPI + Autoencoder PyTorch          │
│  Model loaded in memory                 │
│  Reconstruction error > threshold       │
│  → ANOMALY ALERT                        │
└─────────────────────────────────────────┘
         ↓ WebSocket
┌─────────────────────────────────────────┐
│  Streamlit Live Dashboard               │
│  Real-time metrics + charts + alerts    │
└─────────────────────────────────────────┘
```

---

##  Results

| Metric | Autoencoder | Isolation Forest |
|--------|-------------|-----------------|
| **AUC-ROC** | **0.96** | 0.86 |
| Training Time | ~6 min | 5.6 sec |
| Anomaly Rate (P95) | 5.0% | 1.8% |
| Model Correlation | 0.477 | 0.477 |

### Port Scan Detection Test

| Metric | Normal Traffic | Port Scan Attack |
|--------|---------------|-----------------|
| Reconstruction Error | ~0.09 | **~0.95** |
| Detection |   Normal |   **100% ANOMALY** |
| Threshold | 0.149 | **6x exceeded** |

---

##  Tech Stack

| Category | Technology |
|----------|-----------|
| **Deep Learning** | PyTorch 2.12 |
| **Machine Learning** | Scikit-learn (Isolation Forest, StandardScaler) |
| **API** | FastAPI + Uvicorn |
| **Real-Time** | Redis + WebSocket |
| **Containerization** | Docker + Docker Compose |
| **Dashboard** | Streamlit + Plotly |
| **Network Capture** | Wireshark/tshark |
| **Virtual Lab** | VirtualBox + Vagrant |
| **Dataset** | CESNET-TimeSeries24 (Zenodo) |

---

##  Project Structure

```
cesnet-anomaly-detection/
├── data/
│   ├── cesnet_sample.csv          # Combined CESNET dataset
│   ├── X_train.pkl / X_test.pkl   # Preprocessed ML data
│   ├── test_sample.csv            # Quick test file (100 rows)
│   └── capture_*.csv              # Wireshark captures
├── models/
│   ├── autoencoder.pth            # Trained PyTorch model
│   ├── isolation_forest.pkl       # Baseline model
│   ├── scaler.pkl                 # StandardScaler
│   └── config.json                # Threshold + features config
├── notebooks/
│   ├── 01_EDA.ipynb               # Exploratory Data Analysis
│   ├── 02_Autoencoder.ipynb       # Model training
│   └── 03_Comparison.ipynb        # Model comparison
├── api/
│   └── main.py                    # FastAPI + WebSocket endpoints
├── dashboard/
│   └── app.py                     # Streamlit live dashboard
├── utils/
│   ├── predictor.py               # predict() function
│   ├── wireshark_to_cesnet.py     # Wireshark → CESNET converter
│   ├── realtime_producer.py       # Redis producer
│   └── test_wireshark.py          # Pipeline test
├── notes/                         # Weekly summaries + VM config
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── Vagrantfile
└── README.md
```

---

##  Quick Start

### Prerequisites

- Docker Desktop
- Anaconda / Python 3.10
- VirtualBox + Vagrant

### 1. Clone & Setup

```bash
git clone https://github.com/hiba255/cesnet-anomaly-detection.git
cd cesnet-anomaly-detection
conda create -n cesnet python=3.10
conda activate cesnet
pip install -r requirements.txt
```

### 2. Launch Docker Services

```bash
docker-compose up -d
```

This starts:
- **FastAPI** on `http://localhost:8000`
- **Redis** on `localhost:6379`

### 3. Launch Dashboard

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501`

### 4. Launch Virtual Lab (Real-Time Mode)

```bash
# Terminal 1 — Start VMs
vagrant up

# Terminal 2 — Start traffic capture on VM1
vagrant ssh vm1
while true; do tshark -i enp0s8 -a duration:10 -T fields \
  -e ip.src -e ip.dst -e ip.proto -e frame.len \
  -e tcp.dstport -e udp.dstport -e ip.ttl \
  -e frame.time_delta -e tcp.flags -e ip.len \
  -e frame.time_epoch -e tcp.srcport -e udp.srcport \
  -E header=y -E separator=, \
  > /vagrant/data/realtime_capture.csv 2>/dev/null; sleep 1; done

# Terminal 3 — Start Redis producer
python utils/realtime_producer.py

# Terminal 4 — Generate attack traffic (optional)
vagrant ssh vm1
while true; do nmap -p 1-5000 192.168.56.20; sleep 5; done
```

---

##  API Documentation

Full interactive docs at `http://localhost:8000/docs`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API status |
| `/health` | GET | Model health check |
| `/model-info` | GET | Architecture details |
| `/predict` | POST | Analyze CSV file |
| `/ws/realtime` | WebSocket | Live anomaly stream |

### Example: Predict via curl

```bash
curl -X POST "http://localhost:8000/predict" \
  -F "file=@data/test_sample.csv"
```

### Example Response

```json
{
  "total_connections": 100,
  "anomalies_detected": 5,
  "normal_connections": 95,
  "anomaly_rate": 5.0,
  "threshold": 0.1494,
  "results": [
    {"row": 1, "label": "normal", "error": 0.082},
    {"row": 2, "label": "anomalie", "error": 0.651}
  ]
}
```

---

##  Real-Time Pipeline

### How it works

1. **tshark** captures network traffic every 10 seconds on VM1
2. **wireshark_to_cesnet.py** aggregates packets into 12 CESNET features per minute per IP
3. **realtime_producer.py** pushes flows to Redis queue every 5 seconds
4. **FastAPI WebSocket** (`/ws/realtime`) consumes Redis, runs Autoencoder inference
5. **Streamlit dashboard** receives results via WebSocket and updates live

### Anomaly Detection Logic

```
Reconstruction Error = MSE(input, autoencoder(input))

if error > threshold (0.1494):
    → ANOMALY 
else:
    → NORMAL 
```

The threshold is the **95th percentile** of reconstruction errors on normal training data.

---

##  Dataset

**CESNET-TimeSeries24** — Published in *Scientific Data (Nature), 2025*

| Property | Value |
|----------|-------|
| Source | CESNET3 ISP network, Czech Republic |
| Period | 40 weeks, 275,000+ active IPs |
| Download | [Zenodo Record 13382427](https://zenodo.org/records/13382427) |
| Files Used | `ip_addresses_sample.tar.gz` (~170MB) |
| Format | CSV time series, 10-minute windows |
| Features | 12 network flow features per IP per window |

### The 12 Features

| Feature | Description |
|---------|-------------|
| `n_flows` | Number of distinct connections |
| `n_packets` | Total packets sent/received |
| `n_bytes` | Total bytes exchanged |
| `n_dest_ip` | Number of distinct destination IPs |
| `n_dest_ports` | Number of distinct destination ports |
| `n_dest_asn` | Number of distinct destination networks |
| `tcp_udp_ratio_packets` | TCP vs UDP ratio (packets) |
| `tcp_udp_ratio_bytes` | TCP vs UDP ratio (bytes) |
| `dir_ratio_packets` | Outgoing vs total ratio (packets) |
| `dir_ratio_bytes` | Outgoing vs total ratio (bytes) |
| `avg_duration` | Average connection duration (seconds) |
| `avg_ttl` | Average Time-To-Live value |

---

##  Author

**Hiba** — Data Science & AI Intern  
Project: Network Anomaly Detection System  
Dataset: CESNET-TimeSeries24 | Model: Autoencoder PyTorch  

---

##  License

This project was developed as part of an internship. Dataset usage follows [CESNET-TimeSeries24 license terms](https://zenodo.org/records/13382427).
