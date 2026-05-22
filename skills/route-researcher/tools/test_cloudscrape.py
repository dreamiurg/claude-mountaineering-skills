"""Tests for cloudscrape.py

Unit tests with mocked HTTP / render path — no real browser launched.
"""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from cloudscrape import cli


class TestDefaultPath:
    """Tests for the default (non-render) HTTP fetch path."""

    def test_success_returns_html_to_stdout(self):
        """Successful fetch prints HTML to stdout and exits 0."""
        runner = CliRunner()
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()

        with patch("cloudscrape.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = runner.invoke(cli, ["https://example.com"])

        assert result.exit_code == 0
        assert "<html>" in result.output

    def test_network_error_exits_0_with_note(self):
        """Network failure exits 0 (graceful degradation) with a JSON note."""
        runner = CliRunner()

        with patch("cloudscrape.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.side_effect = Exception("Connection refused")
            mock_client_cls.return_value = mock_client

            result = runner.invoke(cli, ["https://example.com"])

        assert result.exit_code == 0
        # Should output a JSON error note (to stdout or stderr — either is fine per contract)
        # At minimum the process must not crash with exit code != 0
        data = json.loads(result.output)
        assert "error" in data or "note" in data

    def test_http_error_exits_0_with_note(self):
        """HTTP 4xx/5xx exits 0 (graceful degradation) with a JSON note."""
        import httpx

        runner = CliRunner()

        with patch("cloudscrape.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "403 Forbidden",
                request=MagicMock(),
                response=MagicMock(status_code=403),
            )
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = runner.invoke(cli, ["https://example.com"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "error" in data or "note" in data


class TestRenderPath:
    """Tests for the --render Patchright-backed path."""

    def test_render_flag_routes_to_render_path(self):
        """--render flag uses the render path (not plain HTTP)."""
        runner = CliRunner()

        with patch("cloudscrape._fetch_with_render") as mock_render:
            mock_render.return_value = "<html>rendered</html>"
            result = runner.invoke(cli, ["https://example.com", "--render"])

        mock_render.assert_called_once()
        assert result.exit_code == 0
        assert "rendered" in result.output

    def test_render_forwards_default_timeout(self):
        """--render passes the default timeout (30) to _fetch_with_render."""
        runner = CliRunner()

        with patch("cloudscrape._fetch_with_render") as mock_render:
            mock_render.return_value = "<html/>"
            runner.invoke(cli, ["https://example.com", "--render"])

        mock_render.assert_called_once_with("https://example.com", 30)

    def test_render_forwards_custom_timeout(self):
        """--render --timeout 60 passes 60 to _fetch_with_render."""
        runner = CliRunner()

        with patch("cloudscrape._fetch_with_render") as mock_render:
            mock_render.return_value = "<html/>"
            runner.invoke(cli, ["https://example.com", "--render", "--timeout", "60"])

        mock_render.assert_called_once_with("https://example.com", 60)

    def test_render_failure_exits_0_with_note(self):
        """Render path failure exits 0 (graceful degradation) with a JSON note."""
        runner = CliRunner()

        with patch("cloudscrape._fetch_with_render") as mock_render:
            mock_render.side_effect = Exception("Patchright not available")
            result = runner.invoke(cli, ["https://example.com", "--render"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "error" in data or "note" in data

    def test_render_patchright_import_error_exits_0(self):
        """If patchright is not installed, exits 0 with a JSON note."""
        runner = CliRunner()

        with patch("cloudscrape._fetch_with_render") as mock_render:
            mock_render.side_effect = ImportError("No module named 'patchright'")
            result = runner.invoke(cli, ["https://example.com", "--render"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "error" in data or "note" in data


class TestCLIContract:
    """Tests that verify the documented CLI contract is preserved."""

    def test_url_is_required_positional_argument(self):
        """URL is a required positional argument; omitting it exits non-zero."""
        runner = CliRunner()
        result = runner.invoke(cli, [])
        assert result.exit_code != 0

    def test_timeout_option_accepted(self):
        """--timeout option is accepted without error."""
        runner = CliRunner()
        mock_response = MagicMock()
        mock_response.text = "<html/>"
        mock_response.raise_for_status = MagicMock()

        with patch("cloudscrape.httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.get.return_value = mock_response
            mock_client_cls.return_value = mock_client

            result = runner.invoke(cli, ["https://example.com", "--timeout", "60"])

        assert result.exit_code == 0
