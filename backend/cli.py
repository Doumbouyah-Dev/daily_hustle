import click
from flask.cli import AppGroup
from werkzeug.security import generate_password_hash
from app import db  # Import your db instance
from app.models import Users, UserRole # Import your Users model and UserRole enum

# Create a custom Flask CLI group for user management
user_cli = AppGroup('user')

@user_cli.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
def create_admin(username, email, password):
    """
    Creates a new admin user.
    Example: flask user create-admin myadmin admin@example.com StrongP@ssw0rd
    """
    # Check if a user with the given username or email already exists
    existing_user = Users.query.filter(
        (Users.username == username) | (Users.email == email)
    ).first()

    if existing_user:
        click.echo(f"Error: User with username '{username}' or email '{email}' already exists.")
        return

    # Create the new Admin user
    new_admin = Users(
        username=username,
        email=email,
        firstname="Super",
        lastname="Admin",
        role=UserRole.ADMIN,
        is_verified=True, # Admins are typically verified by default
        phone=None, # Optional
        gender=None # Optional
    )
    
    # Hash the password
    new_admin.set_password(password) # This uses the set_password method from your Users model

    db.session.add(new_admin)
    try:
        db.session.commit()
        click.echo(f"Admin user '{username}' created successfully!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Error creating admin user: {e}")