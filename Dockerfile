FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com DJANGO_SUPERUSER_PASSWORD=adminpassword

EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate && python manage.py create_admin && python manage.py runserver 0.0.0.0:8000"]