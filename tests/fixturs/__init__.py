from modules.handlers_files.fixtures import create_upload_file_fixture, create_image_bytes_fixture
from tests.fixturs.fixturs_db import session_db, not_open_session_db
from tests.fixturs.replace_services import user_service_fixture, compression_images_fixture, handler_images_fixture, \
    path_builder_fixture
from tests.fixturs.fixtures import app_fastapi, config_fix, client_for_tests, \
    lifespan_for_tests

from tests.modules.users.fixtures import create_user_fixture
from tests.modules.refresh_tokens.fixtures import create_refresh_token_fixture

__all__ = [
    "lifespan_for_tests",
    "app_fastapi",
    "not_open_session_db",
    "client_for_tests",

    # Р‘Р” С„РёРєСЃС‚СѓСЂС‹
    "config_fix",
    "session_db",

    # СЃРµСЂРІРёСЃС‹
    "user_service_fixture",
    "compression_images_fixture",
    "handler_images_fixture",
    "path_builder_fixture",

    # РёР· РјРѕРґРµР»РµР№
    "create_user_fixture",
    "create_refresh_token_fixture",

    "create_upload_file_fixture",
    "create_image_bytes_fixture",
    "create_splice_material_fixture",
]
from tests.modules.splice_materials.fixtures import create_splice_material_fixture

