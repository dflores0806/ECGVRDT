import numpy as np
import tflite_runtime.interpreter as tflite
import argparse
import requests
import os
import shutil
import datetime

# Configuration
DEFAULT_MODEL_PATH = "ecg_model.tflite"
DEFAULT_DOWNLOAD_URL = "http://localhost:8000/download-tflite"
LOG_PATH = "model_update.log"

# Categorical encodings
RHYTHM_ENCODING = {
    "Sinus": 0,
    "Bradycardia": 1,
    "Tachycardia": 2,
    "Atrial Fibrillation": 3
}

T_WAVE_ENCODING = {
    "Normal": 0,
    "Flattened": 1,
    "Inverted": 2,
    "Peaked": 3
}

CLASSES = [
    "Normal",
    "Bradycardia",
    "Tachycardia",
    "Atrial Fibrillation",
    "Myocardial Infaction",
    "Hearth Block"
]

def predict_ecg_tflite(
    heart_rate, pr_interval, qrs_duration, st_segment,
    qtc_interval, electrical_axis, rhythm_str, t_wave_str,
    model_path=DEFAULT_MODEL_PATH
):
    # Convert categorical inputs
    rhythm = RHYTHM_ENCODING.get(rhythm_str, -1)
    t_wave = T_WAVE_ENCODING.get(t_wave_str, -1)

    if rhythm == -1 or t_wave == -1:
        raise ValueError("Invalid value for Rhythm or T_Wave.")

    input_data = np.array([[
        heart_rate, pr_interval, qrs_duration, st_segment,
        qtc_interval, electrical_axis, rhythm, t_wave
    ]], dtype=np.float32)

    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])[0]

    predicted_index = int(np.argmax(output_data))
    predicted_class = CLASSES[predicted_index]
    confidence = output_data[predicted_index]

    return predicted_class, confidence, output_data

def log_update(message: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def update_model(download_url=DEFAULT_DOWNLOAD_URL, save_path=DEFAULT_MODEL_PATH):
    temp_path = "temp_model.tflite"
    backup_path = None

    try:
        print(f"Downloading updated model from {download_url}...")
        response = requests.get(download_url)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            f.write(response.content)

        print("Download complete. Validating model...")

        # Validate the downloaded model
        try:
            interpreter = tflite.Interpreter(model_path=temp_path)
            interpreter.allocate_tensors()
        except Exception as e:
            os.remove(temp_path)
            error_msg = f"Validation failed: {e}"
            print(error_msg)
            log_update(f"[ERROR] {error_msg} | URL: {download_url}")
            return

        # Backup previous model if it exists
        if os.path.exists(save_path):
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"ecg_model_backup_{timestamp}.tflite"
            shutil.copy(save_path, backup_path)
            print(f"Previous model backed up as '{backup_path}'.")

        # Replace current model
        shutil.move(temp_path, save_path)
        print(f"Model successfully updated and saved to '{save_path}'.")

        # Success log
        log_update(f"[OK] Model updated from {download_url} | Backup: {backup_path or 'None'}")

    except requests.exceptions.RequestException as e:
        error_msg = f"Download failed: {e}"
        print(error_msg)
        log_update(f"[ERROR] {error_msg} | URL: {download_url}")
        
def show_log(log_path=LOG_PATH):
    if not os.path.exists(log_path):
        print("No update log found.")
        return

    print("📄 Model Update Log:")
    with open(log_path, "r") as log_file:
        for line in log_file:
            print(line.strip())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ECG Prediction with TFLite Model on Edge Device")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    log_parser = subparsers.add_parser("log", help="Show model update log")

    # Subcommand: predict
    predict_parser = subparsers.add_parser("predict", help="Run prediction")
    predict_parser.add_argument("--hr", type=float, required=True)
    predict_parser.add_argument("--pr", type=float, required=True)
    predict_parser.add_argument("--qrs", type=float, required=True)
    predict_parser.add_argument("--st", type=float, required=True)
    predict_parser.add_argument("--qtc", type=float, required=True)
    predict_parser.add_argument("--axis", type=float, required=True)
    predict_parser.add_argument("--rhythm", type=str, required=True)
    predict_parser.add_argument("--t_wave", type=str, required=True)
    predict_parser.add_argument("--model", type=str, default=DEFAULT_MODEL_PATH)

    # Subcommand: update
    update_parser = subparsers.add_parser("update", help="Update the TFLite model from remote URL")
    update_parser.add_argument("--url", type=str, default=DEFAULT_DOWNLOAD_URL, help="Download URL")

    args = parser.parse_args()

    if args.command == "predict":
        predicted_class, confidence, _ = predict_ecg_tflite(
            heart_rate=args.hr,
            pr_interval=args.pr,
            qrs_duration=args.qrs,
            st_segment=args.st,
            qtc_interval=args.qtc,
            electrical_axis=args.axis,
            rhythm_str=args.rhythm,
            t_wave_str=args.t_wave,
            model_path=args.model
        )

        print(f"Predicted class: {predicted_class}")
        print(f"Confidence: {confidence * 100:.2f}%")

    elif args.command == "update":
        update_model(download_url=args.url)

    elif args.command == "log":
        show_log()

    else:
        parser.print_help()
