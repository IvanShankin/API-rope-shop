from pathlib import Path

from src.core.config import Config


class PathBuilder:
    def __init__(self, config: Config):
        self.config = config

    @staticmethod
    def _prepare_directory(directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    # --- product ---

    def get_product_original(
        self,
        product_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.products
            / str(product_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_product(
        self,
        product_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.products / str(product_id)
        )

        return root_dir / f"{file_name}.webp"

    def get_product_dir(
        self,
        product_id: int,
    ) -> Path:
        return self.config.paths.products / str(product_id)

    # --- category ---

    def get_category_original(
        self,
        category_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.categories
            / str(category_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_category(
        self,
        category_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.categories / str(category_id)
        )

        return root_dir / f"{file_name}.webp"

    # --- splice_type ---

    def get_splice_type_original(
        self,
        product_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.splice_types
            / str(product_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_splice_type(
        self,
        splice_type_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.splice_types / str(splice_type_id)
        )

        return root_dir / f"{file_name}.webp"

    # --- work_photo ---

    def get_work_photo_original(
        self,
        work_photo_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.work_photos
            / str(work_photo_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_work_photo(
        self,
        work_photo_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.work_photos / str(work_photo_id)
        )

        return root_dir / f"{file_name}.webp"

    # --- charity_photo ---

    def get_charity_photo_original(
        self,
        charity_photo_id: int,
        file_name: str,
        file_type: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.charity_photos
            / str(charity_photo_id)
            / "original"
        )

        return root_dir / f"{file_name}.{file_type}"

    def get_charity_photo(
        self,
        charity_photo_id: int,
        file_name: str,
    ) -> Path:
        root_dir = self._prepare_directory(
            self.config.paths.charity_photos / str(charity_photo_id)
        )

        return root_dir / f"{file_name}.webp"

    # --- temp ---

    def get_temp(self) -> Path:
        return self._prepare_directory(
            self.config.paths.temp
        )
