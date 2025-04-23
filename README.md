ECGTwinMentor is a digital twin system designed to support cardiology education through ECG simulation and AI-based diagnosis. It integrates a deep learning model for ECG prediction and offers a platform for students and professionals to interact with ECG data in an intuitive and educational environment.

## Key Features

- ECG simulation and interactive visualization
- AI-based prediction using a deep learning model
- Deployable on web (cloud), Android, and Raspberry Pi (edge)
- Designed for educational use and offline accessibility

## System Components

- Web application with user-friendly interface (React + FastAPI)
- Embedded AI model for local and cloud-based inference
- ECG simulator for dynamic waveform rendering
- Edge deployments for mobile (Android) and hardware (Raspberry Pi)

## Deployment

### Web (Cloud)

The web version of ECGTwinMentor runs a React frontend connected to a FastAPI backend. It allows remote users to input ECG data, simulate signals, and receive AI-based predictions through a REST API. The system is designed for easy deployment on cloud infrastructure.

### Raspberry Pi (Edge)

A lightweight Python-based tool allows local predictions using a TensorFlow Lite model, with support for offline usage and remote updates.

### Android (Edge)

A Kotlin-based mobile application enables users to enter ECG data, simulate ECG signals, receive predictions, and compare them with manual diagnoses, all directly on the device.

## Authors

 - Daniel Flores-Martin: [dfloresm@unex.es](mailto:dfloresm@unex.es)
 - Francisco Díaz-Barrancas: [frdiaz@unex.es](mailto:frdiaz@unex.es)
 - Javier Berrocal: [jberolm@unex.es](mailto:jberolm@unex.es)
 - Pedro J. Pardo: [pjpardo@unex.es](mailto:pjpardo@unex.es)
 - Juan M. Murillo: [juanmamu@unex.es](mailto:juanmamu@unex.es)