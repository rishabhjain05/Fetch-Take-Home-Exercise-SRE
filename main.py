from __future__ import annotations

import sched
import os
import time
from argparse import ArgumentParser
from typing import Any, Callable, Dict, List
from urllib.parse import urlparse

import requests
import yaml

TIMEOUT_IN_S = 0.5
HEALTH_CHECK_DELAY = 15

class Host:
    def __init__(self, hostname: str) -> None:
        self.hostname: str = hostname
        self.endpoints: List[Endpoint] = []

    def perform_health_check(self) -> str:
        """Return health check summary of all endpoints of host"""
        up_endpoints: int = 0

        # loop through each endpoint and check if it is up
        for endpoint in self.endpoints:
            if endpoint.is_up():
                up_endpoints += 1

        percentage = round(up_endpoints * 100 / len(self.endpoints), 2)

        return f"{self.hostname} has {percentage}% availability percentage"

    def __repr__(self) -> str:
        return f"Host({self.hostname}, endpoints={self.endpoints})"
    
class Endpoint:
    def __init__(
        self, name: str, url: str, method: str = "GET", body: str = None,
        headers: Dict[str, str] = None
    ) -> None:  
        self.name = name
        self.url = url
        self.method = method.upper()
        self.body = body
        self.headers = headers

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Endpoint:
        """Create Endpoint instance from dict"""
        return Endpoint(
            data["name"],
            data["url"],
            method=data.get("method", "GET"),
            body=data.get("body"),
            headers=data.get("headers")
        )

    def is_up(self) -> bool:
        """Sends requests and returns true if endpoint is up.
        
        The endpoint is considered up when response status code is in the
        2XX range and response lantency is less than 500ms.
        """
        req_fn: Callable[[], requests.Response] = None

        if self.method == "GET":    
            req_fn = requests.get
        elif self.method == "POST":
            req_fn = requests.post
        elif self.method == "PUT":
            req_fn = requests.put
        elif self.method == "DELETE":
            req_fn = requests.delete
        elif self.method == "HEAD":
            req_fn = requests.head
        elif self.method == "OPTIONS":
            req_fn = requests.options
        else:
            raise Exception(f"Invalid HTTP method - {self.method}")

        try:
            # send request with timeout
            res = req_fn(
                self.url, headers=self.headers, data=self.body, timeout=TIMEOUT_IN_S
            )

            if res.status_code >= 200 and res.status_code < 300:
                return True
        except requests.exceptions.Timeout as ignored:
            ...
        except Exception as ignored:
            ...
        return False

    def __repr__(self) -> str:
        return f"Endpoint({self.name}, {self.url})"

def read_endpoints(input_file_path: str) -> List[Endpoint]:
    """Reads file and returns list of endpoints"""
    endpoints: List[Endpoint] = []

    with open(input_file_path) as file:
        data: List[Dict] = yaml.safe_load(file)

        for endpoint_data in data:
           endpoints.append(Endpoint.from_dict(endpoint_data))

    return endpoints

def parse_file(input_file_path: str) -> List[Host]:
    """Reads file and returns list of Hosts"""
    endpoints = read_endpoints(input_file_path)
    hosts_map: Dict[str, Host] = {}

    for endpoint in endpoints:
        hostname = urlparse(endpoint.url).hostname
        if hostname not in hosts_map:
            hosts_map[hostname] = Host(hostname)

        hosts_map[hostname].endpoints.append(endpoint)

    return list(hosts_map.values())

def health_check_runner(scheduler: sched.scheduler, hosts: List[Host]):
    scheduler.enter(HEALTH_CHECK_DELAY, 1, health_check_runner, argument=(scheduler, hosts))

    logs = [
        host.perform_health_check()
        for host in hosts
    ]
    
    for log in logs:
        print(log)

def main():
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument("--file-path", required=True, type=str)
    args = parser.parse_args()

    input_file_path: str = args.file_path
    if not os.path.isfile(input_file_path):
        raise FileNotFoundError

    hosts = parse_file(input_file_path)

    # Run scheduler
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, health_check_runner, argument=(scheduler, hosts))
    scheduler.run()


if __name__ == "__main__":
    main()