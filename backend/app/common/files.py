import os
import uuid
from flask import current_app
from app.common.errors import AppError

# Las fotos se validan por CONTENIDO (firma de bytes), no por la extensión ni por el
# Content-Type que envía el cliente. Así un ejecutable renombrado a .jpg se rechaza.
JPEG_SIGNATURE = b"\xff\xd8\xff"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png"}


def detect_image_type(content):
    if content.startswith(JPEG_SIGNATURE):
        return "image/jpeg"
    if content.startswith(PNG_SIGNATURE):
        return "image/png"
    return None


def read_photo_files(files, current_active=0):
    """Valida la lista de archivos recibidos y devuelve [(bytes, mime_type)].

    current_active = fotos activas que ya tiene el objeto (para no pasar de 5).
    """
    max_photos = current_app.config["MAX_PHOTOS_PER_OBJECT"]
    max_bytes = current_app.config["MAX_PHOTO_BYTES"]
    files = [file for file in files if file and file.filename != ""]

    if len(files) == 0:
        raise AppError("Debe adjuntar al menos una fotografía (campo photos).", 400)
    if current_active + len(files) > max_photos:
        raise AppError(f"Un objeto admite máximo {max_photos} fotografías activas.", 400)

    photos = []
    for file in files:
        content = file.read()
        if len(content) == 0:
            raise AppError(f"El archivo {file.filename} está vacío.", 400)
        if len(content) > max_bytes:
            raise AppError(f"El archivo {file.filename} supera el máximo de 5 MB.", 400)
        mime_type = detect_image_type(content)
        if mime_type is None:
            raise AppError(f"El archivo {file.filename} no es una imagen JPEG o PNG válida.", 400)
        photos.append((content, mime_type))
    return photos


def save_photo(content, mime_type):
    """Guarda el archivo con un nombre interno generado (nunca el nombre recibido)."""
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    storage_key = uuid.uuid4().hex + EXTENSIONS[mime_type]
    with open(os.path.join(folder, storage_key), "wb") as photo_file:
        photo_file.write(content)
    return storage_key


def photo_path(storage_key):
    return os.path.join(current_app.config["UPLOAD_FOLDER"], storage_key)


def discard_uncommitted_files(storage_keys):
    """Compensación: si la transacción falla, se retiran los archivos que se alcanzaron
    a escribir para esa operación. Nunca se usa con fotos ya registradas en la base."""
    for storage_key in storage_keys:
        try:
            os.remove(photo_path(storage_key))
        except OSError:
            pass
