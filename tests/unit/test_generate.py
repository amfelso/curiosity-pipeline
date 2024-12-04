from functions.process_mars_metadata import app


def test_process_metadata():
    data = app.lambda_handler(None, "")
    assert 0 <= data["stock_price"] >= 0 <= 100
