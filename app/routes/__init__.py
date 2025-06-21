from flask import Blueprint

# Import all blueprints
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.user import user_bp
from app.routes.home import home_bp

# Optionally, you can use this file to expose a list of blueprints
# all_blueprints = [auth_bp, admin_bp, user_bp, home_bp]
