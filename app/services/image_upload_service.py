import uuid
from fastapi import UploadFile, HTTPException
from pathlib import Path

from app.core.media_config import PRODUCT_IMAGES, CATEGORY_IMAGES


class ImageUploadService:

    def _validate_image(self, file: UploadFile):

        allowed = ["image/jpeg", "image/png", "image/webp"]

        if file.content_type not in allowed:
            raise HTTPException(400, "Invalid image type")

    async def _save(self, file: UploadFile, folder: Path):

        ext = file.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = folder / filename

        content = await file.read()

        with open(path, "wb") as f:
            f.write(content)

        return str(path)

    # =========================
    # PRODUCT IMAGE UPLOAD
    # =========================
    async def upload_product_image(self, file: UploadFile):

        self._validate_image(file)

        path = await self._save(file, PRODUCT_IMAGES)

        return {
            "image_url": path,
            "status": "pending"
        }

    # =========================
    # CATEGORY IMAGE UPLOAD
    # =========================
    async def upload_category_image(self, file: UploadFile):

        self._validate_image(file)

        path = await self._save(file, CATEGORY_IMAGES)

        return {
            "image_url": path,
            "status": "pending"
        }


image_upload_service = ImageUploadService()