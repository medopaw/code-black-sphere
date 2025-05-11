import sys
print(f"Python Executable: {sys.executable}")
print(f"sys.path: {sys.path}")
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
