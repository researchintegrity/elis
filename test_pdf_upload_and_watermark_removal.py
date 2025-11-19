#!/usr/bin/env python
"""
Simple end-to-end test script for PDF upload and watermark removal.

This script:
1. Starts a test user (login/register)
2. Uploads the test PDF
3. Initiates watermark removal for all 3 aggressiveness modes
4. Polls status until completion
5. Displays results

Usage:
    python test_pdf_upload_and_watermark_removal.py

Requirements:
    - FastAPI server running on http://localhost:8000
    - MongoDB running
    - PDF file accessible at: /media/jcardenuto/Windows/Users/phill/work/2025-elis-system/system_modules/watermark-removal/test/10.1371_journal.pone.0003856.pdf
"""

import sys
import time
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_PDF_PATH = "/media/jcardenuto/Windows/Users/phill/work/2025-elis-system/system_modules/watermark-removal/test/10.1371_journal.pone.0003856.pdf"

# Test credentials
TEST_USERNAME = "test_watermark_user"
TEST_EMAIL = "test_watermark@example.com"
TEST_PASSWORD = "TestPassword123"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.BLUE}→ {text}{Colors.RESET}")

def print_step(num, text):
    """Print step marker."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}Step {num}: {text}{Colors.RESET}")

def register_user(username, email, password):
    """Register a new test user."""
    print_step(1, "Registering test user")
    
    url = f"{API_BASE_URL}/auth/register"
    payload = {
        "username": username,
        "email": email,
        "password": password,
        "full_name": "Test Watermark User"
    }
    
    try:
        response = requests.post(url, json=payload)
        
        if response.status_code in [200, 201]:
            print_success(f"User registered: {username}")
            return response.json()
        elif response.status_code == 400:
            # User might already exist, try login instead
            print_info("User may already exist, attempting login...")
            return None
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
        return None

def login_user(username, password):
    """Login user and get auth token."""
    print_step(2, "Logging in user")
    
    url = f"{API_BASE_URL}/auth/login"
    payload = {
        "username": username,
        "password": password
    }
    
    try:
        # Login requires form data, not JSON
        response = requests.post(url, data=payload)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_success(f"User logged in: {username}")
            print_info(f"Token: {token[:20]}...")
            return token
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Login error: {str(e)}")
        return None

def upload_pdf(token, pdf_path):
    """Upload PDF document."""
    print_step(3, "Uploading PDF document")
    
    if not Path(pdf_path).exists():
        print_error(f"PDF file not found: {pdf_path}")
        return None
    
    file_size = Path(pdf_path).stat().st_size
    print_info(f"File: {Path(pdf_path).name}")
    print_info(f"Size: {file_size / 1024:.1f} KB")
    
    url = f"{API_BASE_URL}/documents/upload"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, headers=headers)
        
        if response.status_code in [200, 201]:
            data = response.json()
            # The schema has id with alias _id
            doc_id = data.get("id") or data.get("_id")
            print_success(f"PDF uploaded successfully")
            print_info(f"Document ID: {doc_id}")
            return doc_id
        else:
            print_error(f"Upload failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Upload error: {str(e)}")
        return None

def initiate_watermark_removal(token, doc_id, mode):
    """Initiate watermark removal for a document."""
    url = f"{API_BASE_URL}/documents/{doc_id}/remove-watermark"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"aggressiveness_mode": mode}
    
    print_info(f"Calling: {url}")
    print_info(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code in [200, 201, 202]:
            data = response.json()
            task_id = data.get("task_id")
            status = data.get("status")
            print_success(f"Mode {mode}: Watermark removal initiated")
            print_info(f"Task ID: {task_id}")
            print_info(f"Status: {status}")
            return task_id
        else:
            print_error(f"Mode {mode}: Failed to initiate removal - {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Mode {mode}: Error initiating removal - {str(e)}")
        return None

def get_watermark_removal_status(token, doc_id):
    """Get watermark removal status."""
    url = f"{API_BASE_URL}/documents/{doc_id}/watermark-removal/status"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print_error(f"Error getting status: {str(e)}")
        return None

def wait_for_completion(token, doc_id, timeout=300, poll_interval=2):
    """Wait for watermark removal to complete."""
    print_step(5, "Waiting for watermark removal to complete")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status_data = get_watermark_removal_status(token, doc_id)
        
        if not status_data:
            print_error("Failed to get status")
            return None
        
        status = status_data.get("status", "unknown")
        
        if status == "completed":
            print_success("Watermark removal completed!")
            return status_data
        elif status == "failed":
            error = status_data.get("error", "Unknown error")
            print_error(f"Watermark removal failed: {error}")
            return status_data
        elif status in ["not_started", "queued"]:
            print_info(f"Status: {status}... waiting...")
        else:
            print_info(f"Status: {status}... ({time.time() - start_time:.0f}s)")
        
        time.sleep(poll_interval)
    
    print_error(f"Timeout waiting for completion after {timeout} seconds")
    return None

def remove_watermarks(token, doc_id):
    """Remove watermarks with all three modes."""
    print_step(4, "Initiating watermark removal for all modes")
    
    results = {}
    
    for mode in [1, 2, 3]:
        print(f"\n  Mode {mode}:")
        task_id = initiate_watermark_removal(token, doc_id, mode)
        results[mode] = {"task_id": task_id}
        time.sleep(1)  # Small delay between requests
    
    return results

def display_results(token, doc_id, mode_results):
    """Display final results."""
    print_header("Watermark Removal Results")
    
    status_data = get_watermark_removal_status(token, doc_id)
    
    if status_data:
        print(f"Document ID: {status_data.get('document_id')}")
        print(f"Overall Status: {status_data.get('status')}")
        print(f"Mode: {status_data.get('aggressiveness_mode')}")
        
        if status_data.get('status') == 'completed':
            print(f"\n{Colors.GREEN}Completion Details:{Colors.RESET}")
            print(f"  Output Filename: {status_data.get('output_filename')}")
            print(f"  Output Size: {status_data.get('output_size'):,} bytes")
            print(f"  Cleaned Document ID: {status_data.get('cleaned_document_id')}")
            print(f"  Completed At: {status_data.get('completed_at')}")
        elif status_data.get('error'):
            print(f"\n{Colors.RED}Error:{Colors.RESET}")
            print(f"  {status_data.get('error')}")
    
    print()

def main():
    """Main test execution."""
    print_header("PDF Upload & Watermark Removal Test")
    
    # Check if API is available
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code != 200:
            print_error(f"API not responding properly. Status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {API_BASE_URL}")
        print_info("Make sure the FastAPI server is running:")
        print_info("  cd /media/jcardenuto/Windows/Users/phill/work/2025-elis-system")
        print_info("  source uvenv/bin/activate")
        print_info("  uvicorn app.main:app --reload")
        return False
    
    print_success(f"API is available at {API_BASE_URL}")
    
    # Register user
    register_user(TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD)
    
    # Login
    token = login_user(TEST_USERNAME, TEST_PASSWORD)
    if not token:
        print_error("Failed to obtain authentication token")
        return False
    
    # Upload PDF
    doc_id = upload_pdf(token, TEST_PDF_PATH)
    if not doc_id:
        print_error("Failed to upload PDF")
        return False
    
    # Remove watermarks (all modes)
    mode_results = remove_watermarks(token, doc_id)
    
    # Wait for completion
    status_data = wait_for_completion(token, doc_id)
    
    # Display results
    display_results(token, doc_id, mode_results)
    
    if status_data and status_data.get('status') == 'completed':
        print_header("Test Completed Successfully!")
        print_success("Watermark removal workflow completed successfully")
        return True
    else:
        print_header("Test Failed")
        print_error("Watermark removal did not complete successfully")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
