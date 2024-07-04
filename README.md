# Lostarmour web scrapper

Это репозиторий проекта, посвященный летней практике 2024 в АО "ИТТ".

## Структура микросервиса

> [!TIP]
> На текущий момент репозиторий содержит микросервис, написанный на FastAPI и MongoDB. Он имеет следующие "ручки".

1. **POST** `/load_html_document`:
```json
{
  "armclass": "",
  "path_to_document": ""
}
```
Доступны все классы, используемые сервисом [lostarmour.info](https://lostarmour.info/armour): `"tank"`, `"bmp"` и другие.

На выходе получаем путь к сохраненному HTML-документу.

2. **POST** `/cache_lostarmour_data`:
```json
{
  "path_to_document": ""
}
```
В json указываем путь к сохраненному документу. 

Ничего не возвращает, заполняет БД согласно поднятому контейнеру.

3. **POST** `/download_images`:
```json
{
  "armour_names": ["Т-72А", ...],
  "path_to_images": ""
}
```
Необходимо указать список желаемой бронетехники, а также путь, по которому будут сохранены изображения.

На выходе получаем директорию, куда сохранены изображения.

## Инструкция по эксплуатации

1. Создаем виртуальное окружение.

Unix:
```sh
python -m venv .venv
source .venv/bin/activate
```

Windows:
```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

2. Устанавливаем зависимости.

```sh
cd src
pip install -r requirements.txt
```

3. Поднимаем сервер.

```sh
fastapi dev server.py
```

4. Запускаем докер с базой.

```sh
docker-compose up -d
docker exec -i -t mongodb bash
mongosh -u "user" -p "pass"
use lostarmour_store
```
