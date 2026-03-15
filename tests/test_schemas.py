from pydantic import ValidationError
import pytest

from src.shortener.schemas import ShortURLCreate


class TestSSRFValidation:
    def test_valid_public_url(self):
        schema = ShortURLCreate(original_url="https://example.com")
        assert schema.original_url is not None

    def test_localhost_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://localhost/admin")

    def test_loopback_ip_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://127.0.0.1/secret")

    def test_private_network_10_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://10.0.0.1/internal")

    def test_private_network_172_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://172.16.0.1/internal")

    def test_private_network_192_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://192.168.1.1/router")

    def test_aws_metadata_blocked(self):
        with pytest.raises(ValidationError, match="private or reserved"):
            ShortURLCreate(original_url="http://169.254.169.254/latest/meta-data/")

    def test_ftp_scheme_blocked(self):
        with pytest.raises(ValidationError):
            ShortURLCreate(original_url="ftp://example.com/file")

    def test_javascript_scheme_blocked(self):
        with pytest.raises(ValidationError):
            ShortURLCreate(original_url="javascript:alert(1)")

    def test_data_scheme_blocked(self):
        with pytest.raises(ValidationError):
            ShortURLCreate(original_url="data:text/html,<script>alert(1)</script>")
