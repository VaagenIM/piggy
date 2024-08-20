run_app() {
  if [ "$AUTO_UPDATE" = "True" ]; then
    echo "Auto update enabled"
    sh /usr/local/bin/auto-update.sh;
  else
    echo "Auto update disabled (AUTO_UPDATE not literal 'True')";
  fi

  gunicorn --bind 0.0.0.0:5000 -t 60 --preload run:app &
  PID=$!
  wait $PID
}

trap 'kill -TERM $PID && wait $PID && echo "SIGTERM received, exiting." && exit 0' TERM
trap 'kill -TERM $PID && wait $PID && echo "SIGHUP received, restarting." && run_app' HUP
run_app