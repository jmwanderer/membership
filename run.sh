#!/bin/bash
cd "$(dirname "$0")" || exit 1
.venv/bin/python ./read_new_waivers.py || exit 1
.venv/bin/python ./process_waivers.py || exit 1
exit 0
