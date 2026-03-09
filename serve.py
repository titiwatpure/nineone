"""สคริปต์สำหรับรันแบบ Production

- ใช้ Waitress (WSGI server) แทนการใช้ Flask dev server
- รองรับการกำหนดพอร์ตจากตัวแปรแวดล้อม PORT (เหมาะกับ PaaS/Container)

รัน:
  python serve.py
"""

import os

from waitress import serve

# นำเข้า Flask app object ชื่อ `app` จาก app.py
from app import app  # noqa: E402


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))

    # Waitress จะเป็นคนรับ request และส่งต่อให้ Flask app
    serve(app, host=host, port=port)


if __name__ == "__main__":
    main()
