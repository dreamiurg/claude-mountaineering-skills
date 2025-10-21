import json
from click.testing import CliRunner
from fetch_avalanche import cli

def test_fetch_avalanche_returns_nwac_data():
    """Test NWAC avalanche forecast fetching"""
    runner = CliRunner()
    result = runner.invoke(cli, ['--region', 'North Cascades'])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert 'source' in data
    assert 'region' in data
