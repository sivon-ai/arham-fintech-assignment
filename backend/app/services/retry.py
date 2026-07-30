import time

import requests


def fetch(url):

    retries=5

    delay=2

    for attempt in range(retries):

        try:

            response=requests.get(url)

            response.raise_for_status()

            return response.json()

        except Exception:

            if attempt==retries-1:

                raise

            time.sleep(delay)

            delay*=2