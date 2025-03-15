# WoW Audit Auto Sims

## Overview
This project automates the process of running Raidbots simulations for World of Warcraft characters and uploads the results to WoW Audit. It utilizes Selenium to navigate Raidbots' web interface, starts simulations, polls for completion, and updates WoW Audit with the best gear wishlist.

## Features
- Fetches character and raid information from WoW Audit.
- Starts Raidbots Droptimizer simulations via a headless browser.
- Polls the simulation job status until completion.
- Uploads the generated wishlist to WoW Audit.
- Processes multiple characters asynchronously.
- The script currently processes only non-healer characters.

## Requirements
- Python 3.8+
- Google Chrome or Firefox
- Required Python packages (see `requirements.txt`)
- WoW Audit API token (set as an environment variable `WOWAUDIT_API_TOKEN`)

## Configuration
The script supports the following environment variables for configuration:

- `WOWAUDIT_API_TOKEN`: Your WoW Audit API token.
- `POLL_INTERVAL`: The interval (in seconds) at which the script polls for simulation completion. Default: `30`.
- `UPDATE_INTERVAL_HOURS`: The interval (in hours) at which character data is updated. Default: `2`.
- `USER_AGENT`: The user agent string used for web requests. Default: `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36`.
- `RAIDBOTS_VERSION`: The version of Raidbots to use. Default: `live`.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/Deltachaos/wowaudit-auto-sims.git
   cd wowaudit-auto-sims
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Ensure Google Chrome and ChromeDriver are installed and accessible in your system path.

## Usage
1. Set up your environment variables:
   ```sh
   export WOWAUDIT_API_TOKEN="your_api_token_here"
   export POLL_INTERVAL=30
   export UPDATE_INTERVAL_HOURS=2
   export USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
   export RAIDBOTS_VERSION="live"
   ```
2. Run the script:
   ```sh
   python main.py
   ```
3. The script will automatically fetch characters, initiate simulations, monitor their progress, and upload results.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributions
Contributions and pull requests are welcome! Feel free to open an issue or suggest improvements.

## Disclaimer
This project is not affiliated with Raidbots or WoW Audit. Use at your own risk.
