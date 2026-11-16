# Распознавание растений: API + мобильное приложение

```
plant_project/
  API_CONTRACT.md        контракт API (общий документ, менять только вдвоём)
  shared/classes.json    список классов (порядок = выходы модели)
  server/                Python: FastAPI-сервер (консольное приложение)
  ml/                    Python: обучение модели (следующий шаг)
  mobile/PlantApp/       C#: .NET MAUI (Models/ и Services/ уже готовы)
```

## Запуск сервера-заглушки

```
cd server
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python main.py serve --port 8000
```

В консоли будет напечатан адрес для телефона. Проверка:

```
curl http://localhost:8000/health
curl -F "file=@photo.jpg" "http://localhost:8000/predict?top_k=3"
python main.py predict photo.jpg
```

Тесты: `cd server && pytest -v`

Windows: при первом запуске разрешите Python доступ в сеть в брандмауэре (частная сеть),
иначе телефон не подключится.
