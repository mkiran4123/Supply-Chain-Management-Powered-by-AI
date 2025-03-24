import uvicorn
import signal
import sys

def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    print("\nShutting down gracefully...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Handle termination signal
    
    try:
        # Run the FastAPI application using uvicorn
        # The first parameter is the module:app_instance format
        # host="0.0.0.0" makes the server accessible from other devices on the network
        # reload=True enables auto-reloading when code changes
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        # Handle keyboard interrupt gracefully
        print("\nShutting down gracefully...")
        sys.exit(0)