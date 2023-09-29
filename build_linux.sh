#!/bin/bash

# Save the current directory
CURRENT_DIR=$(pwd)

echo "Step (1/5)"
echo "Creating virtual environment at project root..."

# Create virtual environment
VENV_NAME=venv
python3 -m venv $VENV_NAME

echo "Done..."
echo ""
echo "Step (2/5)"
echo "Activating virtual environment..."

# Activate the virtual environment
source $VENV_NAME/bin/activate

echo "Done..."
echo ""
echo "Step (3/5)"
echo "Installing dependencies..."

# Install dependencies
pip install -r $CURRENT_DIR/requirements.txt

echo "Done..."
echo ""
echo "Step (4/5)"
echo "Creating launchfile at project root..."

# Create launch.sh
echo "python dashboard/run.py" > $CURRENT_DIR/launch.sh

echo "Done..."
echo ""
echo "Step (5/5)"
echo "Deactivating virtual environment..."

# Deactivate the virtual environment
deactivate
