import pytest
from fastapi.testclient import TestClient

from task_control.back_end.app import app
from task_control.back_end.database import get_session


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    with TestClient(app) as client:
        app.dependency_overrides[get_session] = get_session_override
        yield client

    app.dependency_overrides.clear()


# @pytest.fixture
# def session():
#     engine = create_engine(Settings().DATABESE_URL, poolclass=StaticPool)

#     with Session(engine) as session:
#         yield session
