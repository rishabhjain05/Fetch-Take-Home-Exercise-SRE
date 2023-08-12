## Site Reliability Engineering Take-Home Exercise

### Overview
This program checks the health of HTTP endpoints defined in a YAML configuration file. It tests the endpoints every 15 seconds and logs the cumulative availability percentage for each domain.

### Usage
The program takes one required argument - the path to the YAML config file:

```
python3 -m pip install --upgrade pip
python3 main.py --file-path ./input.yaml
```

The config file contains a list of endpoints to monitor, with required name and URL fields, and optional method, headers, and body fields.

The program tests the endpoints every 15 seconds and logs the cumulative availability percentage for each domain.

### Config File Format

The config file must be a valid YAML file with the following schema:

yaml

```
- name: <string>
  url: <string> 
  method: <string>
  headers: <dict> 
  body: <string>
```
`name` and `URL` are required. `method` defaults to GET. `headers` and `body` are optional.

See the example config below.

### Calculating Availability

Availability percentage is calculated as:

```
availability = (num_up_checks / total_checks) * 100
```

A check is considered UP if:

HTTP status is 2xx
Latency is < 500ms

### Implementation
* Written in Python
* Uses Requests library for HTTP checks
* Logging with the logging module
* Unit tests with pytest
