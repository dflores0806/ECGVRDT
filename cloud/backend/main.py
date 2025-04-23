import os
import io
import uuid
import base64
import json
import matplotlib
import matplotlib.pyplot as plt
import joblib

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from pydantic import BaseModel
import numpy as np
import tensorflow as tf

from Crypto.Cipher import AES

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Model settings
TFLITE_PATH = "ecg_model.tflite"
KERAS_MODEL_PATH = "ecg_model.h5"

# AES settings
SECRET_KEY = b'e4799ebc8be0f6bc973ab7fc966d6d4a'  # 32 bytes for AES-256
IV = b'trEMHBkonQFqJAIA'                          # 16 bytes for AES-CBC

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)
#limiter = Limiter(key_func=get_remote_address, default_limits=["1/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load model and scaler
model = tf.keras.models.load_model("ecg_model.h5")
scaler = joblib.load("scaler.pkl")

class EncryptedRequest(BaseModel):
    data: str  # base64 encoded encrypted data

def decrypt_payload(encrypted_b64: str) -> dict:
    encrypted_bytes = base64.b64decode(encrypted_b64)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, IV)
    decrypted = cipher.decrypt(encrypted_bytes)
    unpadded = decrypted.rstrip(b'\x00').rstrip(b'\x01').rstrip(b'\x02').rstrip(b'\x03').rstrip(b'\x04').rstrip(b'\x05').rstrip(b'\x06').rstrip(b'\x07').rstrip(b'\x08').rstrip(b'\x09').rstrip(b'\x0a').rstrip(b'\x0b').rstrip(b'\x0c').rstrip(b'\x0d').rstrip(b'\x0e').rstrip(b'\x0f')
    return json.loads(unpadded.decode('utf-8'))

# Define label mapping
label_map = {
    0: "Atrial Fibrillation",
    1: "Bradycardia",
    2: "Heart Block",
    3: "Myocardial Infarction",
    4: "Normal",
    5: "Tachycardia"
}

# Encoding dictionaries (must match training)
rhythm_map = {"Sinus": 0, "Bradycardia": 1, "Tachycardia": 2, "Atrial Fibrillation": 3}
twave_map = {"Normal": 0, "Inverted": 1, "Peaked": 2, "Flattened": 3}
matplotlib.use('agg')

class ECGInput(BaseModel):
    Heart_Rate: float
    PR_Interval: float
    QRS_Duration: float
    ST_Segment: float
    QTc_Interval: float
    Electrical_Axis: float
    Rhythm: str
    T_Wave: str

def generate_ecg_image(data, cycles: int = 3) -> str:
    fs = 1000
    cycle_duration = 60 / float(data['Heart_Rate'])
    samples_per_cycle = int(fs * cycle_duration)
    t = np.linspace(0, cycle_duration, samples_per_cycle)

    def synthetic_ecg(t, pr, qrs, qt, st):
        pr = float(pr)
        qrs = float(qrs)
        qt = float(qt)
        st = float(st)

        ecg = np.zeros_like(t)
        p_start = int(0.1 * fs)
        p_peak = p_start + int(0.04 * fs)
        qrs_start = p_start + int(pr / 1000 * fs)
        qrs_peak = qrs_start + int(qrs / 2000 * fs)
        t_peak = qrs_start + int(qt / 1000 * fs)

        # función para acceso seguro
        def safe(arr, idx):
            return arr[min(max(0, idx), len(arr) - 1)]

        ecg += np.exp(-((t - safe(t, p_peak)) ** 2) / (2 * (0.015 ** 2))) * 0.1
        ecg += -np.exp(-((t - safe(t, qrs_peak - 5)) ** 2) / (2 * (0.004 ** 2))) * 0.15
        ecg += np.exp(-((t - safe(t, qrs_peak)) ** 2) / (2 * (0.01 ** 2))) * 1.0
        ecg += -np.exp(-((t - safe(t, qrs_peak + 5)) ** 2) / (2 * (0.004 ** 2))) * 0.2
        ecg += np.exp(-((t - safe(t, t_peak)) ** 2) / (2 * (0.04 ** 2))) * 0.3
        return ecg

    ecg_wave = synthetic_ecg(t, data['PR_Interval'], data['QRS_Duration'], data['QTc_Interval'], data['ST_Segment'])
    ecg_long = np.tile(ecg_wave, cycles)
    t_long = np.linspace(0, cycle_duration * cycles, len(ecg_long))

    filename = f"ecg_{uuid.uuid4().hex}.png"
    output_dir = os.path.join(os.path.dirname(__file__), "generated_ecgs")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    #plt.figure(figsize=(12, 3))
    plt.plot(t_long, ecg_long, color='orange', linewidth=2)
    plt.title("Simulated ECG")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (a.u.)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()
    return filepath


def generate_ecg_image_to_buffer(data, buffer, cycles: int = 3):
    fs = 1000
    cycle_duration = 60 / float(data['Heart_Rate'])
    samples_per_cycle = int(fs * cycle_duration)
    t = np.linspace(0, cycle_duration, samples_per_cycle)

    def safe(arr, idx):
        return arr[min(max(0, idx), len(arr) - 1)]

    def synthetic_ecg(t, pr, qrs, qt, st, rhythm, t_wave_type, axis_deg):
        pr = float(pr)
        qrs = float(qrs)
        qt = float(qt)
        st = float(st)

        ecg = np.zeros_like(t)
        p_start = int(0.1 * fs)
        p_peak = p_start + int(0.04 * fs)
        qrs_start = p_start + int(pr / 1000 * fs)
        qrs_peak = qrs_start + int(qrs / 2000 * fs)
        t_peak = qrs_start + int(qt / 1000 * fs)

        # Escalado por tipo de ritmo
        if rhythm == 'Tachycardia':
            rhythm_amp = 0.9
        elif rhythm == 'Bradycardia':
            rhythm_amp = 1.2
        else:
            rhythm_amp = 1.0

        # Amplitud de onda T según tipo
        t_wave_amp = 0.3
        if t_wave_type == 'Inverted':
            t_wave_amp *= -1
        elif t_wave_type == 'Flat':
            t_wave_amp = 0.1

        # Offset por eje eléctrico
        axis_offset = np.sin(np.radians(float(axis_deg))) * 0.2


        ecg += np.exp(-((t - safe(t, p_peak)) ** 2) / (2 * (0.015 ** 2))) * 0.1
        ecg += -np.exp(-((t - safe(t, qrs_peak - 5)) ** 2) / (2 * (0.004 ** 2))) * 0.15
        ecg += np.exp(-((t - safe(t, qrs_peak)) ** 2) / (2 * (0.01 ** 2))) * 1.0
        ecg += -np.exp(-((t - safe(t, qrs_peak + 5)) ** 2) / (2 * (0.004 ** 2))) * 0.2
        ecg += np.exp(-((t - safe(t, t_peak)) ** 2) / (2 * (0.04 ** 2))) * t_wave_amp

        ecg = ecg * rhythm_amp + axis_offset
        return ecg

    ecg_wave = synthetic_ecg(
        t,
        data['PR_Interval'],
        data['QRS_Duration'],
        data['QTc_Interval'],
        data['ST_Segment'],
        data['Rhythm'],
        data['T_Wave'],
        data['Electrical_Axis']
    )

    ecg_long = np.tile(ecg_wave, cycles)
    t_long = np.linspace(0, cycle_duration * cycles, len(ecg_long))

    plt.figure(figsize=(12, 3))
    plt.plot(t_long, ecg_long, color='orange', linewidth=2)
    plt.title("Simulated ECG")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude (a.u.)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(buffer, format='png')
    plt.close()

#############
# ENDPOINTS #
#############

# Predict with uer data    
@app.post("/predict")
@limiter.limit("100/minute")
async def secure_predict(request: Request, ecgdata: EncryptedRequest):
    try:
        # Decrypt data and create ECG object
        decrypted_data = decrypt_payload(ecgdata.data)   
        ecg_input = ECGInput(**decrypted_data)    
        
        x = np.array([[
            ecg_input.Heart_Rate,
            ecg_input.PR_Interval,
            ecg_input.QRS_Duration,
            ecg_input.ST_Segment,
            ecg_input.QTc_Interval,
            ecg_input.Electrical_Axis,
            rhythm_map.get(ecg_input.Rhythm, 0),
            twave_map.get(ecg_input.T_Wave, 0)
        ]])
        x_scaled = scaler.transform(x)
        prediction = model.predict(x_scaled)
        predicted_class = int(np.argmax(prediction))
        label = label_map.get(predicted_class, "Unknown")
        
        # Return prediction result
        return {"prediction": label}

    except Exception as e:
        print("Error=", str(e))
        return {"error": str(e)}

# Generate ECG image
@app.post("/generate-ecg")
@limiter.limit("100/minute")
def generate_ecg(request: Request, ecgdata: EncryptedRequest):
    img_bytes = io.BytesIO()
    
    # Decrypt data and create ECG image
    data = decrypt_payload(ecgdata.data)
    generate_ecg_image_to_buffer(data, img_bytes)
    img_bytes.seek(0)

    # Return ECG image
    return StreamingResponse(img_bytes, media_type="image/png")

# Download tflite model
@app.get("/download-tflite")
@limiter.limit("50/minute")
def convert_and_download_model(request: Request):
    # Verifica si el modelo Keras existe
    if not os.path.exists(KERAS_MODEL_PATH):
        raise HTTPException(status_code=404, detail="Keras model file not found")

    # Convertir el modelo a TensorFlow Lite si aún no existe
    if not os.path.exists(TFLITE_PATH):
        try:
            model = tf.keras.models.load_model(KERAS_MODEL_PATH)
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            tflite_model = converter.convert()
            with open(TFLITE_PATH, "wb") as f:
                f.write(tflite_model)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model conversion failed: {e}")

    # Retornar el archivo como descarga
    return FileResponse(
        path=TFLITE_PATH,
        filename="ecg_model.tflite",
        media_type="application/octet-stream"
    )
