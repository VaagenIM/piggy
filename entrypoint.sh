run_app() {
  gunicorn --bind 0.0.0.0:5000 -t 60 --preload run:app &
  PID=$!
  wait $PID
}

source venv/bin/activate
trap 'kill -TERM $PID && wait $PID && echo "SIGTERM received, exiting." && exit 0' TERM
trap 'kill -TERM $PID && wait $PID && echo "SIGHUP received, restarting." && run_app' HUP
run_app