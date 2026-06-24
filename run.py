from app import create_app, db
from app.models.user import User
from app.models.food_log import FoodLog
from app.models.nutrient import NutrientCache

app = create_app("development")

@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "FoodLog": FoodLog, "NutrientCache": NutrientCache}

@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        print("Database tables created.")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
