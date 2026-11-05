# Un modelo por archivo. Importarlos aquí hace que Flask-Migrate (Alembic) los detecte.
from app.models.role import Role
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.token_revocation import TokenRevocation
from app.models.campus import Campus
from app.models.block import Block
from app.models.department import Department
from app.models.object_category import ObjectCategory
from app.models.object_type import ObjectType
from app.models.person import Person
from app.models.object_lost import ObjectLost
from app.models.object_photo import ObjectPhoto
from app.models.claim import Claim
from app.models.return_record import ReturnRecord
from app.models.audit_log import AuditLog
