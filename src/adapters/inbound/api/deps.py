from fastapi import Request

from src.bootstrap.containers import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container
