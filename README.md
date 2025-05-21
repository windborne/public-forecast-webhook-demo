# Forecast Webhook Demo

This project provides a sample Flask-based web server to download gridded forecast data from the WindBorne Systems API. It allows users to request forecast data for specific models, initialization times, and forecast hours. The server will then download the data in the background and store it as NetCDF files.

## Prerequisites

-   WindBorne Python library (`pip install windborne`)
-   Flask (`pip install Flask`)
-   A WindBorne API key and Client ID. Set these as environment variables:
    -   `WB_CLIENT_ID`
    -   `WB_API_KEY`

    Refer to the [WindBorne API Authentication Documentation](https://windbornesystems.com/docs/api/forecasts#authentication) for more details on obtaining and setting up API credentials.

## Setup and Running

1.  **Ensure `flask_forecast_server.py` is in your project directory.**
2.  **Install dependencies:**
    ```bash
    pip install Flask windborne
    ```
3.  **Set Environment Variables:**
    ```bash
    export WB_CLIENT_ID="YOUR_CLIENT_ID"
    export WB_API_KEY="YOUR_API_KEY"
    ```
    Replace `"YOUR_CLIENT_ID"` and `"YOUR_API_KEY"` with your actual credentials.
4.  **Run the server:**
    ```bash
    python flask_forecast_server.py
    ```
    The server will start on `http://0.0.0.0:8000` by default. You will see output indicating the server has started and where data will be saved.

## Testing with `test_client.py`

This project includes a `test_client.py` script to send sample requests to the running Flask server and verify its basic functionality.

**Prerequisites for running `test_client.py`:**

1.  The Flask forecast server (`flask_forecast_server.py`) must be running (see "Setup and Running" above).
2.  The `requests` library must be installed:
    ```bash
    pip install requests
    ```

**Running the test client:**

Once the server is running, open a new terminal window/tab in the project directory and execute:

```bash
python test_client.py
```

The script will output:
-   The status codes and JSON responses for test POST requests to the `/forecast` endpoint with different models.
-   The JSON response from the `/health` endpoint.
-   The JSON response from the `/status` endpoint.

This helps confirm that the server is responding correctly to different types of requests.

## API Endpoints

### 1. Download Forecast Data

-   **Endpoint:** `/forecast`
-   **Method:** `POST`
-   **Description:** Initiates the download of forecast data.
-   **Request Body (JSON):**
    ```json
    {
        "name": "New forecast",
        "urgency": "low",
        "type": "new_forecast",
        "model": "WeatherMesh",
        "initialization_time": "2025-05-18T00:00:00.000Z",
        "forecast_hours": [1, 2, 3, 6, 12, 24, 48, 72]
    }
    ```
    -   `model` (string, required): The forecast model to use (e.g., "WeatherMesh", "WeatherMesh:deterministic", "WeatherMesh:ens:mean", "WeatherMesh:intracycle"). Refer to WindBorne API documentation for available models.
    -   `initialization_time` (string, required): The initialization time of the forecast in ISO 8601 format (e.g., "YYYY-MM-DDTHH:mm:ssZ" or "YYYY-MM-DDTHH:mm:ss.sssZ").
    -   `forecast_hours` (list of integers, required): A list of forecast hours to download.
    -   `name`, `urgency`, `type` (string, optional): Additional fields that can be sent.

-   **Success Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Forecast download initiated in background."
    }
    ```
-   **Error Response (400 Bad Request):** If required fields are missing.
    ```json
    {
        "error": "Missing required field: model"
    }
    ```
-   **Error Response (500 Internal Server Error):** For other server-side issues.
    ```json
    {
        "error": "Internal server error: <error_details>"
    }
    ```

**Note on Models:**
The `flask_forecast_server.py` currently supports `temperature_2m` variable downloads, but you can easily modify it for others.
- For `"WeatherMesh:ens:mean"`, it sets the `ensemble_member` parameter to `mean`.
- For `"WeatherMesh:intracycle"`, it sets the `intracycle` parameter to `True`.
- For other models like `"WeatherMesh:deterministic"` (or if you send just `"WeatherMesh"`), no extra parameters are added by default for the `get_gridded_forecast` call besides variable, initialization_time, forecast_hour and output_file.

### 2. Health Check

-   **Endpoint:** `/health`
-   **Method:** `GET`
-   **Description:** Checks the health of the server.
-   **Success Response (200 OK):**
    ```json
    {
        "status": "healthy",
        "timestamp": "20XX-XX-XXTXX:00:00Z",
        "data_directory": "data"
    }
    ```

### 3. Status of Downloaded Files

-   **Endpoint:** `/status`
-   **Method:** `GET`
-   **Description:** Lists the NetCDF files currently downloaded in the `data` directory.
-   **Success Response (200 OK):**
    ```json
    {
        "data_directory": "data",
        "total_files": 2,
        "files": [
            "WeatherMesh/2025051800_f001.nc",
            "WeatherMesh/2025051800_f002.nc"
        ]
    }
    ```
    (The `files` list will show subdirectories if models create them)
-   **Error Response (500 Internal Server Error):** If there's an issue accessing the data directory.
    ```json
    {
        "error": "<error_details>"
    }
    ```

## How it Works

When a POST request is made to the `/forecast` endpoint:
1.  The server validates the incoming JSON payload for required fields.
2.  A new thread is spawned to handle the download process for the requested `model`, `initialization_time`, and `forecast_hours`. This ensures the API responds quickly without waiting for downloads to complete.
3.  The `_process_forecast_downloads` function iterates through the `forecast_hours`.
4.  For each hour, `generate_filename` creates a unique filepath based on the model, initialization time, and forecast hour (e.g., `data/WeatherMesh_deterministic/2025052000_fYYY.nc`).
5.  If a file for a specific forecast hour already exists at the target path, the download for that hour is skipped.
6.  Otherwise, it calls the `windborne.get_gridded_forecast` function to download the data.
    - The `variable` is hardcoded to `temperature_2m`.
    - Specific parameters (`ensemble_member`, `intracycle`) are added based on the model name.
7.  Downloaded files are saved as NetCDF (`.nc`) files in the `data` directory, within subfolders named after the model.
8.  Logging provides information about the download progress, successes, skips, and failures.

## File Structure

```
.
├── flask_forecast_server.py  # The main Flask application
├── data/                       # Directory where downloaded .nc files are stored
│   ├── ModelName1/
│   │   ├── YYYYMMDDHH_fXXX.nc
│   │   └── ...
│   └── ModelName2/
│       ├── YYYYMMDDHH_fYYY.nc
│       └── ...
└── README.md                   # This file
```

## WindBorne API Documentation

For more details on the WindBorne API, available models, parameters, and authentication, please refer to the [official documentation.](https://windbornesystems.com/docs/api/forecasts)
