from config.settings import Settings
from core.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host=Settings.HOST, port=Settings.PORT)
