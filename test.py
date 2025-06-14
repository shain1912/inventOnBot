import os
from dotenv import load_dotenv

load_dotenv()  # .env 덮어쓰기 허용

print("태그 값:", os.getenv("ADMIN_ROLE_ID"))  # 또는 int(os.getenv("태그", "0"))
