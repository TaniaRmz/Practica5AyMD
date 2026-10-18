from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "data-raw"
PROCESSED = ROOT / "data" / "data-processed"
NUMERIC = [
    "Global_active_power", "Global_reactive_power", "Voltage",
    "Global_intensity", "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
]
LABELS = {
    "Global_active_power": "Potencia activa (kW)",
    "Global_reactive_power": "Potencia reactiva (kVAR)",
    "Voltage": "Voltaje (V)",
    "Global_intensity": "Intensidad (A)",
    "Sub_metering_1": "Cocina (Wh por minuto)",
    "Sub_metering_2": "Lavandería (Wh por minuto)",
    "Sub_metering_3": "Calentador y aire acondicionado (Wh por minuto)",
}
SOURCE = "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption"
