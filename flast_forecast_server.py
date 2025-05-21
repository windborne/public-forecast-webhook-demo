from flask import Flask, request, jsonify
import os
from datetime import datetime
import logging
from windborne import get_gridded_forecast
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create data directory if it doesn't exist
DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

def generate_filename(initialization_time_str, forecast_hour, model):
    """Returns the path to where the forecast output should be stored"""
    dt_obj = datetime.fromisoformat(initialization_time_str.replace('Z', '+00:00'))
    time_suffix = dt_obj.strftime("%Y%m%d%H")

    # Create filename
    model_folder = model.replace(':', '_')
    filename = f"{model_folder}/{time_suffix}_f{forecast_hour:03d}.nc"

    # Create model folder if it doesn't exist
    model_folder = os.path.join(DATA_DIR, model_folder)
    os.makedirs(model_folder, exist_ok=True)

    return os.path.join(DATA_DIR, filename)

def _process_forecast_downloads(model, initialization_time, forecast_hours):
    """Worker function to process forecast downloads in a separate thread."""
    logger.info(f"Background download started for model: {model}")
    logger.info(f"Forecast hours: {len(forecast_hours)} hours to download")

    downloaded_files = []
    errors = []
    skipped_files = 0

    for forecast_hour in forecast_hours:
        try:
            output_file = generate_filename(initialization_time, forecast_hour, model)

            if os.path.exists(output_file):
                logger.info(f"File {output_file} already exists. Skipping download for forecast hour {forecast_hour}.")
                downloaded_files.append({
                    'forecast_hour': forecast_hour,
                    'filename': output_file,
                    'status': 'skipped'
                })
                skipped_files += 1
                continue

            download_params = {
                'variable': 'temperature_2m',
                'initialization_time': initialization_time,
                'forecast_hour': forecast_hour,
                'output_file': output_file
            }

            if model == "WeatherMesh:ens:mean":
                download_params['ensemble_member'] = 'mean'
            elif model == "WeatherMesh:intracycle":
                download_params['intracycle'] = True
            
            logger.info(f"Downloading forecast hour {forecast_hour}...")
            get_gridded_forecast(**download_params)
            
            downloaded_files.append({
                'forecast_hour': forecast_hour,
                'filename': output_file,
                'status': 'success'
            })
            
        except Exception as e:
            error_msg = f"Failed to download forecast hour {forecast_hour}: {str(e)}"
            logger.error(error_msg)
            errors.append({
                'forecast_hour': forecast_hour,
                'error': str(e)
            })

    # Log completion status
    status_message = {
        'status': 'completed' if not errors else 'partial_success',
        'model': model,
        'initialization_time': initialization_time,
        'total_hours_requested': len(forecast_hours),
        'successful_downloads': len([df for df in downloaded_files if df['status'] == 'success']),
        'skipped_downloads': skipped_files,
        'failed_downloads': len(errors)
    }
    
    if errors:
        logger.warning(f"Background download for model {model} completed with {len(errors)} errors. Details: {status_message}")
    else:
        logger.info(f"Background download for model {model} completed successfully. Details: {status_message}")

@app.route('/forecast', methods=['POST'])
def download_forecast():
    try:
        data = request.get_json()
        
        required_fields = ['model', 'initialization_time', 'forecast_hours']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field} in request: {data}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        model = data['model']
        initialization_time = data['initialization_time']
        forecast_hours = data['forecast_hours']

        logger.info(f"Received forecast request for model: {model}. Queueing for background processing.")
        
        # Start download in a new thread
        # Consider using a queue to limit the number of concurrent downloads
        thread = threading.Thread(target=_process_forecast_downloads, args=(model, initialization_time, forecast_hours))
        thread.start()
        
        return jsonify({'success': True, 'message': 'Forecast download initiated in background.'}), 200
        
    except Exception as e:
        # This will catch errors during request parsing or thread creation
        logger.error(f"Error in /forecast endpoint before starting thread: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data_directory': DATA_DIR
    }), 200

@app.route('/status', methods=['GET'])
def status():
    """Status endpoint showing downloaded files."""
    try:
        files = os.listdir(DATA_DIR)
        nc_files = [f for f in files if f.endswith('.nc')]
        
        return jsonify({
            'data_directory': DATA_DIR,
            'total_files': len(nc_files),
            'files': nc_files
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting Flask server...")
    print(f"Data will be saved to: {os.path.abspath(DATA_DIR)}")
    print(f"Endpoints:")
    print(f"  POST /forecast - Download weather forecasts")
    print(f"  GET  /health   - Health check")
    print(f"  GET  /status   - View downloaded files")
    
    app.run(debug=True, host='0.0.0.0', port=8000)
