"""Combined bounded owner-local CLI. Authored only; never run by offline gates."""
import argparse
import json
import os
import threading
import uuid
from boundary import Authority, load_config
from client import Client
from client_state import OwnerConfig
from model import Failure, identifier
from server import Server


def run_once(config, local_token, upstream_key, request_id):
    # Reject invalid input before server thread/listener or TLS startup.
    identifier(request_id)
    config = OwnerConfig.capture(config).view()
    authority = Authority(config,local_token,upstream_key,'access-'+uuid.uuid4().hex)
    server = Server(authority)
    thread = threading.Thread(target=server.serve,daemon=True)
    client = None
    thread.start()
    try:
        if not server.ready.wait(2) or server.start_error or server.handle is None:
            raise Failure('LOCAL_LISTENER_UNAVAILABLE',502)
        # Non-secret handle remains inside this trusted owner process.
        client = Client(config,local_token,server.handle)
        return client.read(request_id)
    finally:
        if client is not None:
            client.retire()
        server.close()
        thread.join(config.timeout_seconds+1)
        if thread.is_alive():
            raise Failure('LOCAL_TEARDOWN_FAILED',502)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',required=True)
    parser.add_argument('--request-id',required=True)
    args = parser.parse_args()
    try:
        result = run_once(load_config(args.config),os.environ.get('OBSERVATION_LOCAL_TOKEN',''),
                          os.environ.get('OBSERVATION_UPSTREAM_KEY',''),args.request_id)
        print(json.dumps({'status':'ok','coreContract':result['coreContract'],'count':len(result['snapshot']['observations'])}))
    except Failure as error:
        raise SystemExit(error.code) from None

if __name__ == '__main__':
    main()
