"""
Entry point for all SQLAlchemy models in the app.
Ensures all models are imported so Alembic can detect them for migrations.
"""

from app.models.users.user import User
from app.models.users.role import Role
from app.models.users.permission import Permission
from app.models.users.role_permission import RolePermission
from app.models.users.activation_key import ActivationKey

from app.models.products.product import Product
from app.models.products.component import Component
from app.models.products.version import Version

from app.models.bugs.bug import Bug
from app.models.bugs.comment import Comment
from app.models.bugs.attachment import Attachment
from app.models.bugs.tag import Tag
from app.models.bugs.bug_tag import BugTag
