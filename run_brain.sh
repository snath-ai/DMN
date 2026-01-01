#!/bin/bash

# Lár Brain Launcher
# Starts the Cortex (UI) and Autonomic System (Background Daemon)

echo "🧠 Awakening Lár..."

# 1. Start Autonomic Daemon in Background
echo "⚡ Starting Autonomic Nervous System..."
python3 -m src.brain.autonomic_system &
DAEMON_PID=$!

# 2. Start Frontend
echo "👁️ Opening Conscious Interface..."
streamlit run src/lar/app.py

# 3. Cleanup on Exit
kill $DAEMON_PID
echo "💤 Brain Sleeping."
