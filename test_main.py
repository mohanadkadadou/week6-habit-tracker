from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_and_list_habit():
    r = client.post("/habits", json={"name": "Read 20 minutes"})
    assert r.status_code == 200
    hid = r.json()["id"]
    r2 = client.get("/habits")
    assert r2.status_code == 200
    assert any(h["id"] == hid for h in r2.json())


def test_checkin_flow():
    hid = client.post("/habits", json={"name": "Stretch"}).json()["id"]
    r = client.post(f"/habits/{hid}/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 200
    r2 = client.get(f"/habits/{hid}/checkins")
    assert r2.json() == ["2026-09-22"]


def test_checkin_unknown_habit_404():
    r = client.post("/habits/99999/checkin", json={"day": "2026-09-22"})
    assert r.status_code == 404


def test_create_habit_strips_whitespace():
    r = client.post("/habits", json={"name": "  Meditate  "})
    assert r.status_code == 200
    assert r.json()["name"] == "Meditate"


def test_create_habit_rejects_empty_and_blank_names():
    for bad in ["", "   ", "\t\n"]:
        r = client.post("/habits", json={"name": bad})
        assert r.status_code == 422
        assert "name must not be empty" in r.text


def test_create_habit_rejects_overlong_name():
    r = client.post("/habits", json={"name": "x" * 101})
    assert r.status_code == 422
    assert "at most 100" in r.text


def test_create_habit_rejects_missing_name():
    assert client.post("/habits", json={}).status_code == 422


def test_checkin_rejects_malformed_day():
    hid = client.post("/habits", json={"name": "Journal"}).json()["id"]
    for bad in ["", "tomorrow", "2026-9-22", "22-09-2026", "20260922", "2026-13-01", "2026-02-30"]:
        r = client.post(f"/habits/{hid}/checkin", json={"day": bad})
        assert r.status_code == 422, bad
        assert "day" in r.text
    assert client.get(f"/habits/{hid}/checkins").json() == []


def test_checkin_rejects_lookalike_digits_and_trailing_whitespace():
    """Unicode digits, full-width digits, ISO week dates and padding must not be stored."""
    hid = client.post("/habits", json={"name": "Strict days"}).json()["id"]
    for bad in ["٢٠٢٦-٠٩-٢٢", "２０２６-０９-２２", "2026-W39-2", "2026-09-22\n", " 2026-09-22"]:
        r = client.post(f"/habits/{hid}/checkin", json={"day": bad})
        assert r.status_code == 422, bad
    assert client.get(f"/habits/{hid}/checkins").json() == []


def test_stripped_name_is_what_gets_listed():
    hid = client.post("/habits", json={"name": "  Floss  "}).json()["id"]
    assert {"id": hid, "name": "Floss"} in client.get("/habits").json()
