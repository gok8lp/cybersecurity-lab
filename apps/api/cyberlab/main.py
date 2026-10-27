import os
from .service import uygulama, create_app
app = create_app() if os.getenv('CYBERLAB_AUTO') == '1' else None
