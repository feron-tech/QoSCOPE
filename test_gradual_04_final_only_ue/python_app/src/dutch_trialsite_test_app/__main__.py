import uvicorn

if __name__ == "__main__":
    server = uvicorn.Server(
        uvicorn.Config(
            "dutch_trialsite_test_app:app",
            host="0.0.0.0",
            port=80,
        )
    )
    server.run()
