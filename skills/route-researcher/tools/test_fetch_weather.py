import json
from click.testing import CliRunner
from fetch_weather import cli

def test_fetch_weather_returns_forecast():
    """Test weather fetching returns structured forecast"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--peak-name', 'Mt Baker', '--coordinates', '48.7767,-121.8144'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'forecast' in data
    assert 'source' in data
