# Python Telegram Bot Flashcards

[![Unit Test](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/unit_testing.yaml/badge.svg)](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/unit_testing.yaml)
[![Deployment](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/deployment.yaml/badge.svg)](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/deployment.yaml)
[![Current Status](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/current_status.yaml/badge.svg)](https://github.com/ocriado91/python-telegrambot-flashcards/actions/workflows/current_status.yaml)
[![codecov](https://codecov.io/gh/ocriado91/python-telegrambot-flashcards/branch/main/graph/badge.svg?token=bjdlYmQmOw)](https://codecov.io/gh/ocriado91/python-telegrambot-flashcards)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains a Python Telegram Bot that allows users to create and study flashcards within a Telegram chat interface. The bot utilizes the Telegram Bot API and provides a simple and interactive way for users to enhance their learning experience.

## Features

- Create and manage flashcard decks
- Add, edit, and delete flashcards within decks
- Study flashcards in a randomized order
- Keep track of progress and performance

## Commands

- `/new_item`: Add a new item. This item can be a `answer-quiz` text, a two
  columns CSV file to import multiple items at the same time,
  or photo, video or audio with caption as answer.
- `/new_round`: A new quiz round begins!

## Requirements

To run the Python Telegram Bot Flashcards, you'll need the following:

- Python 3.8 or higher

## Installation

### a) From source

1. Clone the repository:

```bash
git clone https://github.com/ocriado91/python-telegrambot-flashcards.git
```
2. Configure the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
3. Configure your Telegram Bot API key

Please, use the official [Telegram Bot](https://core.telegram.org/bots/tutorial) tutorial for setup your own bot, and modify
the `config/template.toml` file with the related information

3. Start the bot:
```bash
python3 src/flashcard.py config/<YOUR_CONFIG_FILE>.toml
```

### b) Using Docker

__NOTE__: It is required to fill the configuration template with your own Telegram Bot API Key. [Futher instructions](https://core.telegram.org/bots/features#botfather). In the following example, a `config.toml` file has been properly modified before to build docker image.

```bash
docker build -t flashcardbot .
docker run --name telegrambot -d flashcardbot python3 src/flashcard.py config/config.toml
```

## Usage
Once the bot is running, you can interact with it directly through your Telegram account. The bot will guide you through the available commands and functionalities.

## Contributing
Contributions to the Python Telegram Bot Flashcards project are welcome! If you encounter any issues or have suggestions for improvement, please create a new issue on the GitHub repository. If you'd like to contribute code, you can fork the repository, make your changes, and submit a pull request.

Please ensure that your code follows the existing coding style and conventions and include relevant tests with your contributions.

## License
This project is licensed under the [MIT License](https://opensource.org/license/mit/).