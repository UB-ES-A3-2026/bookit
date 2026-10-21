# Imatge de desenvolupament del backend (Django + DRF).
FROM python:3.12-slim

# Sense fitxers .pyc i amb la sortida de Python sense buffer (els logs surten al moment).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primer només les dependències, perquè Docker en reaprofiti la capa si el codi canvia.
# S'instal·len les de desenvolupament per poder executar pytest dins del contenidor.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000

# En arrencar, aplica les migracions pendents i aixeca el servidor de desenvolupament,
# que es recarrega quan canvia el codi muntat des de ./backend. Si migrate falla, el servidor no arrenca.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec python manage.py runserver 0.0.0.0:8000"]
