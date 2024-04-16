#!/bin/bash
##################################################################################################
# Bash script to deploy FlashcardBot into a Raspberry Pi server
# More information: https://github.com/ocriado91/python-telegrambot-flashcards/blob/main/README.md
##################################################################################################


# Create a configuration file from template
mkdir secrets/
cp config/template.toml secrets/config.toml
# Replace TelegramBot API Key with variable through Github Actions
echo "Replacing Telegram Bot API"
sed -i "s|<YOUR_API_KEY>|${{ TELEGRAMBOT_API_KEY }}|g" secrets/config.toml
# Export DOCKER_HOST variable
export DOCKER_HOST=ssh://rpimon@rpi-mon-server
# Stop and remove previous docker container
echo "Check previous container..."
docker_containers=$(docker container inspect flashcardbot | wc -l)
if [[ ${docker_containers} -ne 1 ]]; then
    echo "Previous flashcardbot container detected. Stopping it..."
    docker stop flashcardbot
    docker container rm flashcardbot
fi
# Remove previous docker image
echo "Removing previous image"
docker rmi flashcardbot
# Build docker image into Raspberry Pi
docker build -t flashcardbot .
# Run docker container into Raspberry Pi
docker run --name flashcardbot -d flashcardbot python3 src/flashcard.py secrets/config.toml
