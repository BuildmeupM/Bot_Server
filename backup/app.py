from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import os
import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
import logging
import subprocess
import threading
import time
from file_manager import FileManager
from web_automation import WebAutomation

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FileManager and WebAutomation
file_manager = FileManager()
web_automation = WebAutomation()

# Store upload history in memory (in production, use database)
upload_history = []

# Global variables for test management
current_test_process = None
test_output_buffer = []
test_is_running = False

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of files from the bot's file system"""
    try:
        # Get main folders and scan for files
        main_folders = file_manager.get_main_folders()
        files = []
        
        for folder in main_folders:
            # Scan for files in the folder
            for root, dirs, filenames in os.walk(folder):
                for filename in filenames:
                    file_path = Path(root) / filename
                    try:
                        stat = file_path.stat()
                        files.append({
                            'id': len(files) + 1,
                            'name': filename,
                            'size': f"{stat.st_size / 1024:.1f} KB",
                            'type': get_file_type(filename),
                            'lastModified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                            'path': str(file_path.relative_to(file_manager.base_path))
                        })
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
        
        return jsonify({'files': files})
    except Exception as e:
        logger.error(f"Error getting files: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file from the system"""
    try:
        # This is a simplified implementation
        # In a real app, you'd want to map file_id to actual file path
        logger.info(f"Delete file request for ID: {file_id}")
        return jsonify({'message': 'File deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    try:
        # This is a simplified implementation
        # In a real app, you'd want to map file_id to actual file path
        logger.info(f"Download file request for ID: {file_id}")
        return jsonify({'message': 'Download endpoint reached'})
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-to-web', methods=['POST'])
def upload_to_web():
    """Upload file to a website using the bot"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        target_website = request.form.get('target_website', '')
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        upload_path = request.form.get('upload_path', '')
        
        if not all([target_website, username, password, upload_path]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Save uploaded file temporarily
        temp_dir = Path('temp_uploads')
        temp_dir.mkdir(exist_ok=True)
        temp_file_path = temp_dir / file.filename
        file.save(temp_file_path)
        
        try:
            # Use the bot to upload file to website
            success = web_automation.upload_file_to_website(
                target_website=target_website,
                username=username,
                password=password,
                file_path=str(temp_file_path),
                upload_path=upload_path
            )
            
            if success:
                # Record successful upload
                upload_record = {
                    'id': len(upload_history) + 1,
                    'filename': file.filename,
                    'target': target_website,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat(),
                    'message': f'File uploaded successfully to {target_website}'
                }
                upload_history.append(upload_record)
                
                # Clean up temp file
                temp_file_path.unlink()
                
                return jsonify({
                    'message': f'File {file.filename} uploaded successfully to {target_website}',
                    'upload_id': upload_record['id']
                })
            else:
                # Record failed upload
                upload_record = {
                    'id': len(upload_history) + 1,
                    'filename': file.filename,
                    'target': target_website,
                    'status': 'failed',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Upload failed - bot could not complete the task'
                }
                upload_history.append(upload_record)
                
                # Clean up temp file
                temp_file_path.unlink()
                
                return jsonify({'error': 'Upload failed - bot could not complete the task'}), 500
                
        except Exception as e:
            # Clean up temp file
            if temp_file_path.exists():
                temp_file_path.unlink()
            
            # Record failed upload
            upload_record = {
                'id': len(upload_history) + 1,
                'filename': file.filename,
                'target': target_website,
                'status': 'failed',
                'timestamp': datetime.now().isoformat(),
                'message': f'Upload error: {str(e)}'
            }
            upload_history.append(upload_record)
            
            logger.error(f"Upload error: {e}")
            return jsonify({'error': f'Upload error: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in upload_to_web: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-history', methods=['GET'])
def get_upload_history():
    """Get upload history"""
    try:
        return jsonify({'uploads': upload_history})
    except Exception as e:
        logger.error(f"Error getting upload history: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get bot status"""
    try:
        # Get bot status from the bot system
        status = {
            'is_running': True,  # This should come from actual bot status
            'last_activity': datetime.now().isoformat(),
            'active_tasks': 0,
            'total_files_processed': len(upload_history)
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    try:
        # Start the bot
        logger.info("Starting bot...")
        # Add your bot start logic here
        return jsonify({'message': 'Bot started successfully'})
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    try:
        # Stop the bot
        logger.info("Stopping bot...")
        # Add your bot stop logic here
        return jsonify({'message': 'Bot stopped successfully'})
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")
        return jsonify({'error': str(e)}), 500

# New API endpoints for running Python scripts
@app.route('/api/run-test', methods=['POST'])
def run_test():
    """Run Python test scripts and return results"""
    global current_test_process, test_output_buffer, test_is_running
    
    try:
        data = request.get_json()
        test_type = data.get('test_type')
        timestamp = data.get('timestamp')
        logger.info(f"/api/run-test requested | type={test_type} | ts={timestamp}")
        
        if not test_type:
            return jsonify({'error': 'Test type not specified'}), 400
        
        if test_is_running:
            return jsonify({'error': 'Another test is already running'}), 409
        
        # Reset test state
        app.test_results = None
        test_output_buffer = []
        test_is_running = True
        current_test_process = None
        
        # Determine which script to run
        if test_type == 'test_system':
            script_path = 'test_system.py'
        elif test_type == 'start_system':
            script_path = 'start_system.py'
        else:
            return jsonify({'error': 'Invalid test type'}), 400
        
        # Check if script exists
        if not Path(script_path).exists():
            return jsonify({'error': f'Script {script_path} not found'}), 404
        
        # Start test in background thread
        def run_script():
            global current_test_process, test_output_buffer, test_is_running
            
            try:
                start_time = time.time()
                
                # Run the Python script with immediate output - เร็วขึ้นมาก!
                process = subprocess.run(
                    [sys.executable, script_path],
                    capture_output=True,
                    text=True,
                    timeout=30  # Timeout 30 วินาที
                )
                
                execution_time = round(time.time() - start_time, 2)
                
                # Prepare result immediately - ไม่ต้องรอ
                result = {
                    'success': process.returncode == 0,
                    'return_code': process.returncode,
                    'execution_time': execution_time,
                    'output': process.stdout,
                    'error': process.stderr if process.stderr else None,
                    'timestamp': timestamp,
                    'test_type': test_type
                }
                
                # Store result for retrieval - ทันทีที่ script เสร็จ
                app.test_results = result
                logger.info(f"Script {script_path} completed in {execution_time}s")
                
            except subprocess.TimeoutExpired:
                logger.error(f"Script {script_path} timed out after 30 seconds")
                app.test_results = {
                    'success': False,
                    'error': 'Script execution timed out after 30 seconds',
                    'timestamp': timestamp,
                    'test_type': test_type
                }
            except Exception as e:
                logger.error(f"Error running script: {e}")
                app.test_results = {
                    'success': False,
                    'error': str(e),
                    'timestamp': timestamp,
                    'test_type': test_type
                }
            finally:
                current_test_process = None
                test_is_running = False
                logger.info(f"Test {test_type} finished")
        
        # Start background thread
        thread = threading.Thread(target=run_script)
        thread.daemon = True
        thread.start()
        
        # ไม่ต้องรอ - กลับทันที
        response = {
            'message': f'Started {test_type} test',
            'status': 'running',
            'timestamp': timestamp
        }
        logger.info(f"/api/run-test accepted | type={test_type}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error starting test: {e}")
        test_is_running = False
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-status', methods=['GET'])
def get_test_status():
    """Get current test status and results - optimized for speed"""
    global test_is_running, current_test_process, app
    
    # ตรวจสอบผลลัพธ์ก่อน - ถ้ามีให้ส่งกลับทันที
    if hasattr(app, 'test_results') and app.test_results:
        logger.info(f"Returning completed test results for {app.test_results.get('test_type')}")
        return jsonify({
            'status': 'completed',
            'results': app.test_results
        })
    elif test_is_running:
        # ถ้ายังรันอยู่ ให้ส่งสถานะ running
        return jsonify({
            'status': 'running',
            'output': test_output_buffer
        })
    else:
        # ถ้าไม่ได้รันอะไร
        return jsonify({
            'status': 'idle'
        })

@app.route('/api/stop-test', methods=['POST'])
def stop_test():
    """Stop currently running test"""
    global current_test_process, test_is_running
    
    try:
        if current_test_process and test_is_running:
            current_test_process.terminate()
            current_test_process = None
            test_is_running = False
            
            return jsonify({'message': 'Test stopped successfully'})
        else:
            return jsonify({'message': 'No test running'})
            
    except Exception as e:
        logger.error(f"Error stopping test: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-output', methods=['GET'])
def get_test_output():
    """Get real-time test output - optimized for speed"""
    global test_output_buffer, test_is_running
    
    return jsonify({
        'output': test_output_buffer,
        'is_running': test_is_running,
        'timestamp': time.time(),
        'line_count': len(test_output_buffer)
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    """Lightweight health check used by frontend to verify connectivity"""
    return jsonify({
        'ok': True,
        'service': 'BotV3 Backend API',
        'time': datetime.now().isoformat()
    })

def get_file_type(filename):
    """Determine file type based on extension"""
    ext = Path(filename).suffix.lower()
    if ext in ['.py', '.pyc']:
        return 'Python'
    elif ext in ['.json', '.xml', '.yaml', '.yml']:
        return 'Config'
    elif ext in ['.txt', '.log']:
        return 'Text'
    elif ext in ['.pdf']:
        return 'PDF'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
        return 'Image'
    elif ext in ['.mp4', '.avi', '.mov']:
        return 'Video'
    else:
        return 'Other'

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'BotV3 Backend API',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Create temp directory if it doesn't exist
    Path('temp_uploads').mkdir(exist_ok=True)
    
    print("Starting BotV3 Backend API...")
    print("API will be available at: http://localhost:5000")
    print("React app should proxy to this backend")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
