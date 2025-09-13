import requests
import csv
import time
from datetime import datetime

# Modem data URLs
URL_DS_QAM = "http://192.168.100.1/data/dsinfo.asp"
URL_US_QAM = "http://192.168.100.1/data/usinfo.asp"
URL_DS_OFDM = "http://192.168.100.1/data/dsofdminfo.asp"
URL_US_OFDM = "http://192.168.100.1/data/usofdminfo.asp"

CSV_FILE = "modem_stats.csv"

def fetch_json(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def avg(values):
    return sum(values) / len(values) if values else None

def parse_downstream_qam(data):
    if not data:
        return None, None
    powers = [float(ch["signalStrength"]) for ch in data if "signalStrength" in ch]
    snrs = [float(ch["snr"]) for ch in data if "snr" in ch]
    return avg(powers), avg(snrs)

def parse_upstream_qam(data):
    if not data:
        return None
    powers = [float(ch["signalStrength"]) for ch in data if "signalStrength" in ch]
    return avg(powers)

def parse_downstream_ofdm(data):
    if not data:
        return None, None
    powers = [float(ch["plcpower"]) for ch in data if "plcpower" in ch]
    snrs = [float(ch["SNR"]) for ch in data if "SNR" in ch]
    return avg(powers), avg(snrs)

def parse_upstream_ofdm(data):
    if not data:
        return None
    powers = [float(ch["repPower"]) for ch in data if "repPower" in ch]
    # SNR not reported for upstream OFDMA
    return avg(powers)

try:
    with open(CSV_FILE, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Downstream QAM Avg Power (dBmV)",
            "Downstream QAM Avg SNR (dB)",
            "Upstream QAM Avg Power (dBmV)",
            "Downstream OFDM Avg Power (dBmV)",
            "Downstream OFDM Avg SNR (dB)",
            "Upstream OFDMA Avg Power (dBmV)"
        ])
except FileExistsError:
    pass

print("Starting logger... (Ctrl+C to stop)")

while True:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ds_qam = parse_downstream_qam(fetch_json(URL_DS_QAM))
    us_qam = parse_upstream_qam(fetch_json(URL_US_QAM))
    ds_ofdm = parse_downstream_ofdm(fetch_json(URL_DS_OFDM))
    us_ofdm = parse_upstream_ofdm(fetch_json(URL_US_OFDM))

    row = [
        ts,
        f"{ds_qam[0]:.2f}" if ds_qam and ds_qam[0] is not None else None,
        f"{ds_qam[1]:.2f}" if ds_qam and ds_qam[1] is not None else None,
        f"{us_qam:.2f}" if us_qam is not None else None,
        f"{ds_ofdm[0]:.2f}" if ds_ofdm and ds_ofdm[0] is not None else None,
        f"{ds_ofdm[1]:.2f}" if ds_ofdm and ds_ofdm[1] is not None else None,
        f"{us_ofdm:.2f}" if us_ofdm is not None else None,
    ]

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)

    print(f"Logged: {row}")
    time.sleep(60)  # poll every 60 seconds
