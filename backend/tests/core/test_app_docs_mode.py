from unittest.mock import patch
from src.modules.api.app import init_fastapi_app


def test_api_docs_disabled_in_prod():
    with patch("src.modules.api.app.create_config") as mock_create_config:
        mock_config = mock_create_config.return_value
        mock_config.env.mode = "PROD"
        mock_config.cors.allow_origins = ["*"]
        mock_config.cors.allow_origin_regex = None
        mock_config.cors.allow_credentials = True
        mock_config.cors.allow_methods = ["*"]
        mock_config.cors.allow_headers = ["*"]
        mock_config.cors.expose_headers = ["*"]
        mock_config.paths.media = "media"

        app = init_fastapi_app()
        assert app.docs_url is None
        assert app.redoc_url is None
        assert app.openapi_url is None


def test_api_docs_enabled_in_dev_or_test():
    with patch("src.modules.api.app.create_config") as mock_create_config:
        mock_config = mock_create_config.return_value
        mock_config.env.mode = "TEST"
        mock_config.cors.allow_origins = ["*"]
        mock_config.cors.allow_origin_regex = None
        mock_config.cors.allow_credentials = True
        mock_config.cors.allow_methods = ["*"]
        mock_config.cors.allow_headers = ["*"]
        mock_config.cors.expose_headers = ["*"]
        mock_config.paths.media = "media"

        app = init_fastapi_app()
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"
