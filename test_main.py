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


ANCHOR = date(2030, 6, 15)  # fixed "today" so streak tests never depend on the real clock


def _streak(hid, today=ANCHOR):
    return client.get(f"/habits/{hid}/streak", params={"today": today.isoformat()}).json()


def _streak_habit(offsets, anchor=ANCHOR):
    hid = client.post("/habits", json={"name": "Streaky"}).json()["id"]
    for off in offsets:
        day = (anchor - timedelta(days=off)).isoformat()
        assert client.post(f"/habits/{hid}/checkin", json={"day": day}).status_code == 200
    return hid


def test_streak_consecutive_days_including_today():
    hid = _streak_habit([0, 1, 2])
    assert _streak(hid) == {"habit_id": hid, "streak": 3}


def test_streak_stops_at_gap_and_ignores_duplicates():
    hid = _streak_habit([0, 0, 1, 3, 4])
    assert _streak(hid)["streak"] == 2


def test_streak_zero_without_checkin_today():
    hid = _streak_habit([1, 2])
    assert _streak(hid)["streak"] == 0


def test_streak_no_checkins_is_zero():
    hid = _streak_habit([])
    assert _streak(hid)["streak"] == 0


def test_streak_unknown_habit_404():
    assert client.get("/habits/99999/streak").status_code == 404


def test_streak_uses_client_supplied_today():
    """A client in another time zone can pass its own 'today'; the server clock is not used."""
    hid = client.post("/habits", json={"name": "Zone"}).json()["id"]
    for day in ["2030-01-09", "2030-01-10", "2030-01-11"]:
        client.post(f"/habits/{hid}/checkin", json={"day": day})
    assert client.get(f"/habits/{hid}/streak", params={"today": "2030-01-11"}).json()["streak"] == 3
    assert client.get(f"/habits/{hid}/streak", params={"today": "2030-01-12"}).json()["streak"] == 0


def test_streak_rejects_malformed_today():
    hid = client.post("/habits", json={"name": "Bad today"}).json()["id"]
    assert client.get(f"/habits/{hid}/streak", params={"today": "not-a-date"}).status_code == 422


def test_streak_crosses_year_boundary():
    anchor = date(2030, 1, 1)
    hid = _streak_habit([0, 1, 2], anchor)  # 2030-01-01, 2029-12-31, 2029-12-30
    assert _streak(hid, anchor)["streak"] == 3


def test_streak_ignores_other_habits_and_future_days():
    hid = _streak_habit([0, 1])
    _streak_habit([0, 1, 2, 3, 4])  # another habit with a longer run
    client.post(f"/habits/{hid}/checkin", json={"day": (ANCHOR + timedelta(days=1)).isoformat()})
    assert _streak(hid)["streak"] == 2
