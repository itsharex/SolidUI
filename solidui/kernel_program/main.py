#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import sys
import pathlib
import json
import logging
import time

import asyncio
import json
import threading

from queue import Queue

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS  # Import the CORS library

import solidui.kernel_program.kernel_manager as kernel_manager
import solidui.kernel_program.config as config
import solidui.kernel_program.utils as utils
from solidui.config import KERNEL_API_PORT

APP_PORT = KERNEL_API_PORT
base_blueprint = Blueprint("baseurl", __name__, url_prefix="/solidui/kernel")

# Note, only one kernel_manager_process can be active
kernel_manager_process = None

# Use efficient Python queues to store messages
result_queue = Queue()
send_queue = Queue()

messaging = None

# We know this Flask app is for local use. So we can disable the verbose Werkzeug logger
logger = config.get_logger()
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)
fh = logging.FileHandler('solidui/kernel.log')
logger.addHandler(fh)

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)

CORS(app)


def start_kernel_manager():
    global kernel_manager_process

    kernel_manager_script_path = os.path.join(
        pathlib.Path(__file__).parent.resolve(), "kernel_manager.py"
    )
    kernel_manager_process = subprocess.Popen(
        [sys.executable, kernel_manager_script_path]
    )

    # Write PID as <pid>.pid to config.KERNEL_PID_DIR
    os.makedirs(config.KERNEL_PID_DIR, exist_ok=True)
    with open(os.path.join(config.KERNEL_PID_DIR, "%d.pid" % kernel_manager_process.pid), "w") as p:
        p.write("kernel_manager")


def cleanup_kernel_program():
    kernel_manager.cleanup_spawned_processes()


async def start_snakemq():
    global messaging

    messaging, link = utils.init_snakemq(config.IDENT_MAIN)

    def on_recv(conn, ident, message):
        message = json.loads(message.data.decode("utf-8"))

        if message["type"] == "status":
            if message["value"] == "ready":
                logger.debug("Kernel is ready.")
                result_queue.put({
                    "value": "Kernel is ready.",
                    "type": "message"
                })

        elif message["type"] in ["message", "message_raw", "image/png", "image/jpeg"]:
            # TODO: 1:1 kernel <> channel mapping
            logger.debug("%s of type %s" % (message["value"], message["type"]))

            result_queue.put({
                "value": message["value"],
                "type": message["type"]
            })

    messaging.on_message_recv.add(on_recv)
    logger.info("Starting snakemq loop")

    def send_queued_messages():
        while True:
            if send_queue.qsize() > 0:
                message = send_queue.get()
                utils.send_json(messaging,
                                {"type": "execute", "value": message["command"]},
                                config.IDENT_KERNEL_MANAGER
                                )
            time.sleep(0.1)

    async def async_send_queued_messages():
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_queued_messages)

    async def async_link_loop():
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, link.loop)

    # Wrap the snakemq_link.Link loop in an asyncio task
    await asyncio.gather(async_send_queued_messages(), async_link_loop())


@base_blueprint.route("/api", methods=["POST", "GET"])
def handle_request():
    if request.method == "GET":
        # Handle GET requests by sending everything that's in the receive_queue
        results = [result_queue.get() for _ in range(result_queue.qsize())]
        return jsonify({"results": results})
    elif request.method == "POST":
        data = request.json

        logger.info(f"data:{data}")

        send_queue.put(data)

        return jsonify({"result": "success"})


@base_blueprint.route("/restart", methods=["POST"])
def handle_restart():
    cleanup_kernel_program()
    start_kernel_manager()

    return utils.response_format()


app.register_blueprint(base_blueprint)


async def main():
    start_kernel_manager()

    # Run Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.start()

    # Run in background
    await start_snakemq()


def run_flask_app():
    app.run(host="0.0.0.0", port=APP_PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    asyncio.run(main())
