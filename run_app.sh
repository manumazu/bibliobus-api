#!/bin/bash
. venv/bin/activate
export PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT=0
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=0
uvicorn main:app --host 127.0.0.1 --port 8000
