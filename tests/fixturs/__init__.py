from tests.modules.handlers_files.fixtures import (
    create_upload_file_fixture,
    create_image_bytes_fixture,
)
from tests.fixturs.fixturs_db import session_db, not_open_session_db
from tests.fixturs.replace_services import (
    user_service_fixture,
    compression_images_fixture,
    handler_images_fixture,
    image_manager_fixture,
    path_builder_fixture,
    splice_type_service_fixture,
    color_service_fixture,
)
from tests.fixturs.fixtures import (
    app_fastapi,
    config_fix,
    client_for_tests,
    lifespan_for_tests,
)

from tests.modules.users.fixtures import create_user_fixture
from tests.modules.refresh_tokens.fixtures import create_refresh_token_fixture
from tests.modules.splice_materials.fixtures import create_splice_material_fixture
from tests.modules.splice_types.fixtures import (
    create_splice_type_fixture,
    create_splice_type_translation_fixture,
)
from tests.modules.splice_prices.fixtures import create_splice_price_rule_fixture
from tests.modules.colors.fixtures import (
    create_color_fixture,
    create_color_translation_fixture,
)
from tests.modules.rope_products.fixtures import (
    create_rope_product_fixture,
    create_rope_variant_fixture,
)
from tests.modules.rope_product_color.fixtures import create_rope_product_color_fixture
from tests.modules.rope_allowed_splice.fixtures import create_rope_allowed_splice_fixture
from tests.modules.material_groups.fixtures import (
    create_material_group_fixture,
    create_material_group_translation_fixture,
)
from tests.modules.materials.fixtures import (
    create_material_fixture,
    create_material_translation_fixture,
)
from tests.modules.quote_requests.fixtures import (
    create_quote_request_fixture,
    create_quote_rope_item_fixture,
    create_quote_service_item_fixture,
)

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
    "image_manager_fixture",
    "path_builder_fixture",
    "splice_type_service_fixture",
    "color_service_fixture",
    "create_user_fixture",
    "create_refresh_token_fixture",
    "create_upload_file_fixture",
    "create_image_bytes_fixture",
    "create_splice_material_fixture",
    "create_splice_type_fixture",
    "create_splice_type_translation_fixture",
    "create_splice_price_rule_fixture",
    "create_color_fixture",
    "create_color_translation_fixture",
    "create_rope_product_fixture",
    "create_rope_variant_fixture",
    "create_rope_product_color_fixture",
    "create_rope_allowed_splice_fixture",
    "create_material_group_fixture",
    "create_material_group_translation_fixture",
    "create_material_fixture",
    "create_material_translation_fixture",
    "create_quote_request_fixture",
    "create_quote_rope_item_fixture",
    "create_quote_service_item_fixture",
]
