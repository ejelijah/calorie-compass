from streamlit.testing.v1 import AppTest


def test_app_renders_dashboard_without_errors(tmp_path, monkeypatch):
    monkeypatch.setenv("NEO_CAL_DB_PATH", str(tmp_path / "app.db"))

    app = AppTest.from_file("streamlit_app.py").run()

    assert not app.exception
    assert app.title[0].value == "Neo_Cal"
    assert [metric.label for metric in app.metric] == [
        "Calories in",
        "Calories out",
        "Net for the day",
    ]
