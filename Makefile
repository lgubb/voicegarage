.PHONY: dev
.PHONY: doctor

dev:
	cd garage-voice-agent && uv run garage-voice-dev

doctor:
	cd garage-voice-agent && uv run garage-voice-doctor
