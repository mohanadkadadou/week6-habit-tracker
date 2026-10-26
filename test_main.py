from datetime import date, timedelta

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


def _streak_habit(offsets):
    hid = client.post("/habits", json={"name": "Streaky"}).json()["id"]
    for off in offsets:
        day = (date.today() - timedelta(days=off)).isoformat()
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    return hid


def test_streak_consecutive_days_including_today():
    hid = _streak_habit([0, 1, 2])
    assert client.get(f"/habits/{hid}/streak").json() == {"habit_id": hid, "streak": 3}


def test_streak_stops_at_gap_and_ignores_duplicates():
    hid = _streak_habit([0, 0, 1, 3, 4])
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 2


def test_streak_zero_without_checkin_today():
    hid = _streak_habit([1, 2])
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 0


def test_streak_no_checkins_is_zero():
    hid = _streak_habit([])
    assert client.get(f"/habits/{hid}/streak").json()["streak"] == 0


def test_streak_unknown_habit_404():
    assert client.get("/habits/99999/streak").status_code == 404
