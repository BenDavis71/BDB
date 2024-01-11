#!/bin/bash

# Replace "your_host" and "your_port" with the actual host and port you want to check
host="10.0.0.5"
port="8501"

# Check if the port is open using netcat
nc -z "$host" "$port"

# Check the exit status of the previous command
if [ $? -eq 0 ]; then
    echo "Currently running"
else
    echo "Port is closed, starting app again"
    /home/nidiyan/.local/bin/streamlit run /home/nidiyan/BDB/streamlit/PullThePlug.py &
fi
