import json
from click.testing import CliRunner
from calculate_daylight import cli

def test_calculate_daylight_returns_times():
    """Test daylight calculation returns sunrise/sunset"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--date', '2025-10-20', '--coordinates', '48.7767,-121.8144'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'sunrise' in data
    assert 'sunset' in data
    assert 'daylight_hours' in data
