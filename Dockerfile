FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app/

# Install python dependencies from Pip
RUN pip install --no-cache-dir -r requirements.txt

# Install TelegramBot API Python package from source
RUN pip install git+https://github.com/ocriado91/python-telegrambot