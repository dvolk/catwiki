# Catwiki: a simple wiki

- Very simple code base
- Formatting with extended markdown
- Page history
- Recent changes page

## Screenshots

<img src="https://i.imgur.com/GX7EP7w.png" width=250> <img src="https://i.imgur.com/uFxoxxE.png" width=250>

## Installation

You will need mongodb:

    apt install mongodb-server

No further database configuration is needed.

    git clone https://github.com/dvolk/catwiki
    cd catwiki
    virtualenv env
    source env/bin/activate
    pip3 install -r requirements.txt

## Running

    python3 app.py

## Authentication

Catwiki doesn't provide any authentication.

If you want to run a publically accessible catwiki, you can configure your web server to use basic authentication on the catwiki domain.