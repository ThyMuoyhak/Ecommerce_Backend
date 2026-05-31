# routes/__init__.py
from . import auth
from . import products
from . import categories
from . import orders
from . import payment

__all__ = ["auth", "products", "categories", "orders", "payment"]