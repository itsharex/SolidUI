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

import importlib
import logging
import pkgutil
from typing import Any

import click
from colorama import Fore, Style
from flask.cli import FlaskGroup, with_appcontext
from solidui import app, cli
from solidui.cli.lib import normalize_token
from solidui.extensions import db

@click.group(
    cls=FlaskGroup,
    context_settings={"token_normalize_func": normalize_token},
)

@with_appcontext
def solidui() -> None:
    """This is a management script for the SolidUI application."""

    @app.shell_context_processor
    def make_shell_context() -> dict[str, Any]:
        return {"app": app, "db": db}




if __name__ == "__main__":
    solidui()
