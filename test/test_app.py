import json, pytest
from app import create_app, DataInstance
from pathlib import Path


### Status Codes ###
OKAY = 200
BAD_REQUEST = 400
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405


### Configure Test Environment ###
RECEIPTS_DIR = Path(DataInstance.PROJECT_DIR, "test", "receipts")


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


### Tests ###
def test_assert():
    assert 42 == 42


def test_receipt_process_get(client):
    response = client.get("/receipts/process")
    assert response.status_code == METHOD_NOT_ALLOWED


def test_receipt_process_post1(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "morning-receipt.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == OKAY and "id" in response.json


def test_receipt_process_post2(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "simple-receipt.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == OKAY and "id" in response.json


def test_receipt_process_post3(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "receipt1.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == OKAY and "id" in response.json


def test_receipt_process_post4(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "receipt2.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == OKAY and "id" in response.json


def test_receipt_process_post__malformed1_400(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "malformed-receipt1.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == BAD_REQUEST


def test_receipt_process_post__malformed2_400(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "malformed-receipt2.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == BAD_REQUEST


def test_receipt_process_post__malformed3_400(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "malformed-receipt3.json")))
    response = client.post("/receipts/process", json=receipt)
    assert response.status_code == BAD_REQUEST


def test_receipts_points_get1(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "receipt1.json")))
    receipt_id = client.post("/receipts/process", json=receipt).json["id"]
    response = client.get(f"/receipts/{receipt_id}/points")
    assert response.status_code == OKAY and response.json["points"] == 28


def test_receipts_points_get2(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "receipt2.json")))
    response = client.post("/receipts/process", json=receipt)
    receipt_id = response.json["id"]
    response = client.get(f"/receipts/{receipt_id}/points")
    assert response.status_code == OKAY and response.json["points"] == 109


def test_receipts_points_get3(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "morning-receipt.json")))
    response = client.post("/receipts/process", json=receipt)
    receipt_id = response.json["id"]
    response = client.get(f"/receipts/{receipt_id}/points")
    assert response.status_code == OKAY and response.json["points"] == 15


def test_receipts_points_get4(client):
    receipt = json.load(open(Path(RECEIPTS_DIR, "simple-receipt.json")))
    response = client.post("/receipts/process", json=receipt)
    receipt_id = response.json["id"]
    response = client.get(f"/receipts/{receipt_id}/points")
    assert response.status_code == OKAY and response.json["points"] == 31


def test_receipts_points_get_malformed_id_404(client):
    response = client.get("/receipts/DEADBEEF/points")
    assert response.status_code == NOT_FOUND


def test_receipts_points_get_not_exist_404(client):
    response = client.get("/receipts/deadbeef-dead-beef-dead-beefdeadbeef/points")
    assert response.status_code == NOT_FOUND


def test_receipts_points_post(client):
    response = client.post("/receipts/DEADBEEF/points", json={
        "data": "Lorem ipsum dolor"
    })
    assert response.status_code == METHOD_NOT_ALLOWED
