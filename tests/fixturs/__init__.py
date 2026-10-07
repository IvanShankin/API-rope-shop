from modules.handlers_files.fixtures import create_upload_file_fixture, create_image_bytes_fixture
from tests.fixturs.fixturs_db import session_db, not_open_session_db
from tests.fixturs.replace_services import user_service_fixture, compression_images_fixture, handler_images_fixture, \
    path_builder_fixture
from tests.fixturs.fixtures import app_fastapi, config_fix, client_for_tests, \
    lifespan_for_tests

from tests.modules.users.fixtures import create_user_fixture
from tests.modules.refresh_tokens.fixtures import create_refresh_token_fixture
from tests.modules.splice_materials.fixtures import create_splice_material_fixture
from tests.modules.splice_types.fixtures import create_splice_type_fixture
from tests.modules.splice_prices.fixtures import create_splice_price_rule_fixture

__all__ = [
    "lifespan_for_tests",
    "app_fastapi",
    "not_open_session_db",
    "client_for_tests",
    "config_fix",
    "session_db",
    "user_service_fixture",
    "compression_images_fixture",
    "handler_images_fixture",
    "path_builder_fixture",
    "create_user_fixture",
    "create_refresh_token_fixture",
    "create_upload_file_fixture",
    "create_image_bytes_fixture",
    "create_splice_material_fixture",
    "create_splice_type_fixture",
    "create_splice_price_rule_fixture",
]
