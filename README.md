# FleetDM Compliance Check

FleetDM Compliance Check is a web application for evaluating host compliance with predefined policies in FleetDM. It allows users to view policy compliance and host details through a Flask-based web interface.

## Features

- Retrieves host information from FleetDM by IP address.
- Evaluates compliance with critical and non-critical policies.
- Provides both HTML and JSON endpoints for compliance data.
- Handles cases where the host is offline or not found.

## Requirements

- Python 3.7+
- FleetDM instance with configured policies.
- An environment variable `CREDENTIALS_DIRECTORY` pointing to the directory containing the API token file `checkmy-token`.
- Flask and required Python dependencies (see `requirements.txt`).

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Toxa/fleetdm-complianceCheck.git
   cd fleetdm-complianceCheck
   ```

2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment variable `CREDENTIALS_DIRECTORY` to point to the directory containing the FleetDM API token file (`checkmy-token`).

   Example:

   ```bash
   export CREDENTIALS_DIRECTORY=/path/to/token/directory
   ```

4. Ensure the token file exists at the specified location and contains a valid FleetDM API token.

## Usage

1. Start the Flask application:

   ```bash
   python app.py
   ```

2. Access the web interface by visiting `http://<server-ip>:5000/` in your browser.

3. The application automatically retrieves the client IP address and evaluates its compliance status.

### API Endpoints

#### Main Page (`/`)
- Displays compliance information in HTML format.
- Automatically detects the client IP and fetches host details.

#### Update Policies (`/update-policies`)
- Method: GET
- Returns JSON data with updated compliance information after a forced refetch.

### Example

To view compliance for a specific host, ensure the host's IP matches the client IP detected by the server.

## Output

The application provides:

- **Critical Policies**: Policies critical to host compliance.
- **Non-Critical Policies**: Informational policies.
- **Access Granted**: Indicates whether the host meets critical policy requirements.
- **Host Details**: Includes hostname, platform, UUID, and more.

## Error Handling

- If the host is not found, a message is displayed with troubleshooting steps.
- If the host is offline, the last seen time is shown.

## Contributing

Contributions are welcome! If you encounter issues or have ideas for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
