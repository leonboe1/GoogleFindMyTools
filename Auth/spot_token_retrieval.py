#
#  GoogleFindMyTools - A set of tools to interact with the Google Find My API
#  Copyright © 2024 Leon Böttger. All rights reserved.
#

from Auth.token_retrieval import request_token
from Auth.username_provider import get_username

cached_spot_token = None

def get_spot_token(username):

    global cached_spot_token

    if cached_spot_token:
        print("[SpotTokenRetrieval] Using Cached Spot Token.")
        return cached_spot_token

    cached_spot_token = request_token(username, "spot", True)
    return cached_spot_token

if __name__ == '__main__':
    print(get_spot_token(get_username()))