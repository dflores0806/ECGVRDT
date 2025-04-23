
import React, { useState } from "react";
import axios from "axios";
import CryptoJS from "crypto-js";

const secretKey = "e4799ebc8be0f6bc973ab7fc966d6d4a"; // Must be 32 characters for AES-256
const iv = CryptoJS.enc.Utf8.parse("trEMHBkonQFqJAIA"); // Must be 16 characters

// Encrypt data
function encryptData(data) {
  const jsonData = JSON.stringify(data);
  const encrypted = CryptoJS.AES.encrypt(jsonData, CryptoJS.enc.Utf8.parse(secretKey), {
    iv: iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7
  });
  return encrypted.toString(); // Base64-encoded
}


const diagnoses = [
  "Normal", "Bradycardia", "Tachycardia", "Atrial Fibrillation", "Myocardial Infarction", "Heart Block",
];
const rhythms = ["Sinus", "Bradycardia", "Tachycardia", "Atrial Fibrillation"];
const tWaves = ["Normal", "Inverted", "Peaked", "Flattened"];

export default function ECGPrediction() {
  const [ecgImage, setEcgImage] = useState(null);
  const [inputs, setInputs] = useState({
    Heart_Rate: "", PR_Interval: "", QRS_Duration: "", ST_Segment: "",
    QTc_Interval: "", Electrical_Axis: "", Rhythm: "Sinus", T_Wave: "Normal",
  });
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null);
  const handleDiagnosisClick = (diagnosis) => setSelectedDiagnosis(diagnosis);
  const [modelPrediction, setModelPrediction] = useState(null);
  const [exampleDiagnosis, setExampleDiagnosis] = useState(null);

  const handleChange = (e) => setInputs({ ...inputs, [e.target.name]: e.target.value });
  const handlePredict = async () => {
    try {
      console.log(inputs)
      const encryptedPayload = { data: encryptData(inputs) };
      const res = await axios.post("http://localhost:8000/predict", encryptedPayload, {
        headers: {
          "Content-Type": "application/json"
        }
      });
      setModelPrediction(res.data.prediction);
    } catch (error) {
      console.error("Prediction error:", error);
    }
  };
  const handleGenerateImage = async () => {
    try {
      const encryptedPayload = { data: encryptData(inputs) };
      const res = await axios.post("http://localhost:8000/generate-ecg", encryptedPayload, {
        headers: {
          "Content-Type": "application/json",
        },
        responseType: "blob",
      });
      const imageUrl = URL.createObjectURL(res.data);
      setEcgImage(imageUrl);
    } catch (error) {
      console.error("ECG image generation error:", error);
    }
  };
  const getRandomFromArray = (arr) => arr[Math.floor(Math.random() * arr.length)];
  const fillExampleValues = () => {
    const diagnosis = getRandomFromArray(diagnoses);
    setInputs({
      Heart_Rate: (60 + Math.random() * 60).toFixed(1),
      PR_Interval: (120 + Math.random() * 80).toFixed(1),
      QRS_Duration: (80 + Math.random() * 40).toFixed(1),
      ST_Segment: (-1 + Math.random() * 3).toFixed(2),
      QTc_Interval: (360 + Math.random() * 100).toFixed(1),
      Electrical_Axis: (-30 + Math.random() * 150).toFixed(1),
      Rhythm: getRandomFromArray(rhythms),
      T_Wave: getRandomFromArray(tWaves),
    });
    setExampleDiagnosis(diagnosis);
    setModelPrediction(null);
  };

  return (
    <div className="container bg-white p-4 rounded shadow mt-4">
      <h1 className="text-center text-primary mb-4">ECGTwinMentor</h1>
      <p className="description">
        This tool simulates an ECG digital twin. Enter or generate typical ECG parameters,
        select the diagnosis you believe is correct, and compare it to the model prediction.
        <br />
        Parameters include: Heart Rate, PR Interval, QRS Duration, ST Segment, QTc Interval,
        Electrical Axis, Rhythm and T-Wave.
      </p>
      <div className="row">
        {Object.entries(inputs).map(([key, value]) => (
          <div key={key} className="col-md-6 mb-3">
            <label className="form-label fw-bold">{key.replace("_", " ")}</label>
            {key === "Rhythm" ? (
              <select name={key} value={value} onChange={handleChange} className="form-control">
                <option value="Atrial Fibrillation">Atrial Fibrillation</option>
                <option value="Bradycardia">Bradycardia</option>
                <option value="Sinus">Sinus</option>
                <option value="Tachycardia">Tachycardia</option>
              </select>
            ) : key === "T_Wave" ? (
              <select name={key} value={value} onChange={handleChange} className="form-control">
                <option value="Flattened">Flattened</option>
                <option value="Inverted">Inverted</option>
                <option value="Normal">Normal</option>
                <option value="Peaked">Peaked</option>
              </select>
            ) : (
              <input
                name={key}
                value={value}
                onChange={handleChange}
                className="form-control"
                placeholder={key}
              />
            )}
          </div>
        ))}
      </div>

      <h5 className="mt-4">Select Your Diagnosis:</h5>
      <div className="d-flex flex-wrap gap-2 mb-4">
        {diagnoses.map((d) => (
          <button
            key={d}
            onClick={() => handleDiagnosisClick(d)}
            className={`btn ${selectedDiagnosis === d ? "btn-primary" : "btn-outline-primary"}`}
          >
            {d}
          </button>
        ))}
      </div>

      <div className="d-flex gap-3 justify-content-center my-4 flex-wrap">
        <button onClick={handlePredict} className="btn btn-success px-4">Check</button>
        <button onClick={handleGenerateImage} className="btn btn-warning px-4">Generate ECG Image</button>
        <button onClick={fillExampleValues} className="btn btn-secondary px-4">Fill Example Values</button>
      </div>

      {ecgImage && (
        <div className="text-center mt-4">
          <h4>Simulated ECG</h4>
          <img src={ecgImage} alt="ECG Simulation" style={{ maxWidth: "100%", border: "1px solid #ccc" }} />
        </div>
      )}

      {exampleDiagnosis && (
        <p className="text-center text-muted">Example filled using <strong>{exampleDiagnosis}</strong> profile.</p>
      )}

      {modelPrediction && (
        <div className="alert alert-light border mt-4">
          <p><strong>Model Prediction:</strong> {modelPrediction}</p>
          <p><strong>User Diagnosis:</strong> {selectedDiagnosis || "None"}</p>
          <p>
            <strong>Result:</strong>{" "}
            {selectedDiagnosis === modelPrediction ? (
              <span className="text-success">Correct ✅</span>
            ) : (
              <span className="text-danger">Incorrect ❌</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}
