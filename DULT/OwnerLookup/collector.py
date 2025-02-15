#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

import csv
import time
from binascii import unhexlify
from datetime import datetime
import os
import struct
import requests
from DULT.OwnerLookup.link_generator import getOwnerLoopUpLink
from example_data_provider import get_example_data


def check_url_for_404(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            html_string = response.text
            contains_404 = "404" in html_string
            contains_error = "error" in html_string
            return contains_404 and contains_error
        else:
            return True
    except requests.RequestException:
        return True


if __name__ == '__main__':

    seconds = 0
    interval = 1024
    csv_file = 'Results/eid_scan_results.csv'
    current_iteration = 0

    last_start_time = seconds

    # Get current UNIX timestamp
    start_date = int(datetime.now().timestamp())

    while True:
        found_non_404 = False
        results = []

        # Start at the last known time offset that was successful - 20 seconds (to account for some randomness)
        current_tried_offset = max(0, last_start_time - 20*interval)

        failed_attempts = 0

        # Print that a new iteration started, as well as the current date
        print(f"New iteration started at {datetime.now()} with offset {current_tried_offset}")

        while True:
            (eid, url) = getOwnerLoopUpLink(unhexlify(get_example_data("sample_identity_key")), current_tried_offset)
            success = not check_url_for_404(url)
            print(f"Time Offset: {current_tried_offset}, EID: {eid}, URL: {url}, Success: {success}")

            if success:
                # found first non-404
                if not found_non_404:
                    print("Found first non-404 URL at time offset:", current_tried_offset)
                    last_start_time = current_tried_offset
                    found_non_404 = True

                failed_attempts = 0
                results.append((current_iteration, current_tried_offset))
            elif found_non_404:
                # try again up to 10 times
                print("Trying again...")
                failed_attempts += 1

            if success or not found_non_404:
                current_tried_offset += interval

            if failed_attempts >= 3:
                print("Failed 3 times.")
                break

            # sleep 10 seconds +- random 0-5 seconds
            time.sleep(10 + struct.unpack('I', os.urandom(4))[0] % 6)

        # Write results to CSV
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            for result in results:
                writer.writerow(result)

        # Get current UNIX timestamp
        current_time = int(datetime.now().timestamp())
        current_iteration += interval

        sleepTime = interval - (current_time - start_date) % interval

        print(f"Sleeping for {sleepTime} seconds")

        # Wait until the next interval
        time.sleep(sleepTime)