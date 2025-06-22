from app import db
from app.models.user import User

admin = User(
    username='admin',
    email='admin@gmail.com',
    role='admin'
)
admin.set_password('admin123')
db.session.add(admin)
db.session.commit()
