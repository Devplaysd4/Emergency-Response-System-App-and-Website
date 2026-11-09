# Secured Yatra — Emergency Response System

> A 2025 hackathon project exploring safer travel through emergency communication, location-aware alerts, incident reporting, and trip planning.

Secured Yatra combines a Python-based mobile application with a Flask-powered website and admin dashboard. Travellers can raise SOS alerts, submit location-tagged incident reports, view travel itineraries, and access location-based safety information. Administrators can monitor incoming alerts and review submitted reports.

## Project links

| Resource | Link |
|---|---|
| Live website / demo | **[Add link here]** |
| Mobile app download | **[Add link here]** |
| Demo video | **[Add link here]** |
| Project presentation | **[Add link here]** |

## Features

- **SOS emergency alerts:** Send an SOS request with available location coordinates and registered emergency details.
- **Fall-detection prompt:** Monitor accelerometer readings for a possible fall pattern and allow an SOS to be triggered.
- **Geofencing:** Use location coordinates and a GeoJSON map layer to support location-boundary warnings.
- **Incident reporting:** Submit a photograph, reason, user details, and location for an incident/anomaly report.
- **Admin dashboard:** View incoming SOS alerts and submitted reports; accept or reject reports.
- **Travel itineraries:** Browse destination-based, day-wise itineraries and select a trip.
- **City safety score:** Retrieve a locally stored safety score for the detected city.

## System overview

### Mobile application
Built with **Python, Kivy, and KivyMD**. The app includes splash, welcome, registration, login, home, profile, itinerary, and safety-score screens. Device integrations use **Plyer** for location, camera, and accelerometer access where supported.

### Website and admin dashboard
Built with **HTML, CSS, and JavaScript**, and served through Flask. The public-facing website introduces Secured Yatra, its safety features, map content, and travel itineraries. The admin interface fetches SOS alerts and incident reports from the backend and provides report-review actions.

### Backend API
The Flask server handles registration, login, SOS submissions, incident reports, and administrative report actions.

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Serve the main website |
| `/register` | POST | Register a user |
| `/login` | POST | Look up a registered user by mobile number |
| `/sos` | POST | Receive and store an SOS alert |
| `/sos_alerts` | GET | Return stored SOS alerts |
| `/report` | POST | Receive a photo-based incident report |
| `/get_reports` | GET | Return submitted incident reports |
| `/accept_report` | POST | Mark a report as accepted |
| `/delete_report` | POST | Delete a report and its uploaded image |

## Technology stack

| Component | Technologies |
|---|---|
| Mobile application | Python, Kivy, KivyMD |
| Web frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Device and location access | Plyer, Geocoder |
| Maps and geospatial data | Kivy Garden MapView, GeoJSON, Folium, OpenStreetMap Nominatim |
| Data storage | JSON files |
| HTTP requests | Requests |

## How it works

1. A traveller registers and signs in through the mobile app.
2. The app can retrieve the user's available location and display map, safety, and itinerary information.
3. During an emergency, the traveller triggers an SOS. The app sends the alert payload to the Flask backend.
4. The backend timestamps and stores the alert. The admin dashboard periodically retrieves alerts and displays them.
5. A traveller can submit an incident report with a photo, description/reason, user information, and coordinates.
6. An administrator reviews submitted reports and can accept or reject them.

## Getting started

### Prerequisites

- Python 3 and pip
- A compatible environment for Kivy/KivyMD
- Android device permissions and compatible hardware for mobile GPS, camera, and accelerometer features

### 1. Clone the repository

```bash
git clone https://github.com/Devplaysd4/Emergency-Response-System-App-and-Website.git
cd Emergency-Response-System-App-and-Website
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install Flask requests Kivy KivyMD plyer geocoder folium
```

Kivy and its supporting libraries may require platform-specific system packages or compatible versions.

### 4. Start the Flask server

```bash
python server.py
```

Open the local URL printed by Flask to access the web application.

### 5. Start the mobile application

In a compatible Kivy environment:

```bash
python amain.py
```

The mobile app uses the `BASE_URL` configured in `amain.py`. For local development, change it to the network-reachable address of your Flask server.

## Key repository files

| File / directory | Description |
|---|---|
| `amain.py` | Kivy/KivyMD mobile application |
| `server.py` | Flask backend and API routes |
| `utils.py` | Location helper |
| `MAIN.html`, `styles.css` | Main website |
| `admin.html`, `admin.css`, `admin.js` | Admin dashboard |
| `*.kv` | Kivy interface layouts |
| `alerts.json` | Sample alert content |
| `itineraries.json` | Destination itinerary data |
| `safety_scores.json` | City safety-score data |
| `website/` | Web resources, map data, reports, and uploads |

## Screenshots

_Add screenshots of the mobile app, website, map view, and admin dashboard._

| Mobile application | Website |
|---|---|
| ![Mobile app](LINK_TO_MOBILE_SCREENSHOT) | ![Website](LINK_TO_WEBSITE_SCREENSHOT) |

## Notes and limitations

- This is a **hackathon prototype**, not a production emergency-response service. Do not rely on it instead of contacting local emergency services.
- GPS, camera, accelerometer, and map functionality depend on platform support, permissions, and device hardware.
- The current backend uses JSON files for persistence. A production system should use a database, robust authentication and authorization, input validation, secure file handling, and operational monitoring.
- The SHA-256 value derived from a mobile number is used as an identifier in the current implementation; it should not be described as a blockchain implementation or identity verification.
- The geofence currently uses approximate coordinate bounds and should not be treated as an authoritative risk map.
- The safety-score lookup uses a local dataset and may not represent real-time risk.

## Team and acknowledgements

Developed as a **2025 hackathon project**.

- **Team members:** [Add names here]
- **Hackathon / institution:** [Add event or institution here]

## Contact

- **GitHub:** [Devplaysd4](https://github.com/Devplaysd4)
- **Email:** [Add contact email]

---

<p align="center">Built with the goal of making journeys safer through connected technology.</p>
