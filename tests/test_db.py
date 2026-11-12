from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connected:", result.scalar())

except Exception as e:
    print("Database connection failed:", e)

finally:
    engine.dispose()