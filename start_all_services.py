"""
Start All E-Commerce Services
"""

import subprocess
import time
import sys
import os

def start_services():
    """Start all microservices"""
    
    print("🚀 STARTING E-COMMERCE SERVICES")
    print("="*50)
    
    # Path to Python executable
    python_exe = "D:/02_Interests (Up Skilling )/Combined Project/venv/Scripts/python.exe"
    base_dir = "d:/02_Interests (Up Skilling )/Combined Project"
    
    services = [
        ("User Service", "user_service.py", 5001),
        ("Product Service", "product_service.py", 5002), 
        ("Order Service", "order_service.py", 5003),
        ("Payment Service", "payment_service.py", 5004),
        ("Notification Service", "notification_service.py", 5005)
    ]
    
    processes = []
    
    try:
        for name, filename, port in services:
            print(f"🔄 Starting {name} on port {port}...")
            
            # Start the service
            process = subprocess.Popen(
                [python_exe, os.path.join(base_dir, filename)],
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            processes.append((name, process, port))
            time.sleep(2)  # Wait a bit between starts
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {name} started successfully")
            else:
                print(f"❌ {name} failed to start")
                stdout, stderr = process.communicate()
                print(f"   Error: {stderr.decode()}")
        
        print(f"\n🎉 ALL SERVICES STARTED!")
        print("="*50)
        print("Services running on:")
        for name, process, port in processes:
            if process.poll() is None:
                print(f"✅ {name}: http://localhost:{port}")
            else:
                print(f"❌ {name}: FAILED")
        
        print("\n🔍 Testing services...")
        
        # Keep services running
        print("\n⏳ Services are running. Press Ctrl+C to stop all services.")
        
        try:
            while True:
                time.sleep(1)
                # Check if any process died
                for name, process, port in processes:
                    if process.poll() is not None:
                        print(f"⚠️ {name} stopped unexpectedly")
        except KeyboardInterrupt:
            print("\n🛑 Stopping all services...")
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")
    
    finally:
        # Stop all processes
        for name, process, port in processes:
            if process.poll() is None:
                print(f"🔄 Stopping {name}...")
                process.terminate()
                process.wait()
        
        print("✅ All services stopped.")

if __name__ == "__main__":
    start_services()
