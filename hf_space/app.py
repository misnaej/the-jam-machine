"""HuggingFace Space entry point for The Jam Machine."""

from __future__ import annotations

from jammy.app.playground import demo

demo.launch(server_name="0.0.0.0", server_port=7860)  # noqa: S104
