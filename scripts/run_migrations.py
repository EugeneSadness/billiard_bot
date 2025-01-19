import os
from alembic import command
from alembic.config import Config

def main():
    # Получаем абсолютный путь к корню проекта
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Создаем конфиг, указывая путь к alembic.ini
    alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))
    
    # Устанавливаем script_location в конфиге
    alembic_cfg.set_main_option("script_location", os.path.join(project_root, "alembic"))
    
    # Применяем миграции
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    main() 