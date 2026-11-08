# Laboratorio 8 — Implementación de Servicios Web con Django

**Curso:** Desarrollo de Aplicaciones Empresariales (4-C24-A)
**Alumno:** Michael Montgomery Rosell

API REST del proyecto de cuestionarios (`Exam`, `Question`, `Choice`) con Django REST Framework.

## Puesta en marcha (Windows, PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_quiz        # usuario demo / demo12345 y datos de prueba
python manage.py test             # 14 pruebas
python manage.py runserver
```

- API navegable: http://127.0.0.1:8000/api/ (inicia sesión en `/api-auth/login/` para escribir)
- Cliente HTTP externo: `python scripts/http_client_check.py` (o `requests.http` con la extensión REST Client de VS Code)

## Estructura

```
config/              settings.py (bloque REST_FRAMEWORK), urls.py
quiz/models.py       Exam, Question, Choice
quiz/serializers.py  ModelSerializer + validación propia
quiz/views.py        tres ModelViewSet (filtro y búsqueda)
quiz/urls.py         DefaultRouter
quiz/tests.py        pruebas de operaciones, errores, filtro y paginación
scripts/http_client_check.py   recorrido por HTTP con códigos de estado
```

## Decisiones (pasos 2 y 4)

- **Paginación:** `PageNumberPagination`, `PAGE_SIZE = 5` (pequeño a propósito para ver más de una página con los datos de prueba).
- **Permisos de partida:** `IsAuthenticatedOrReadOnly`: cualquiera lee, solo un usuario autenticado escribe. Autenticación por sesión (API navegable) y Basic (clientes externos).
- **Relaciones:** las **opciones viajan anidadas** dentro de la pregunta (no tienen sentido solas); el **examen se refiere por su identificador** (`"exam": 1`) porque es un recurso independiente.
- **Validación propia (paso 5):** `QuestionSerializer.validate_choices` rechaza toda pregunta que no tenga **exactamente una** opción correcta. Al modificar `choices` se reemplaza el conjunto completo para que la regla siga cumpliéndose.

## Tabla de la API (paso 11)

Base: `/api`. La escritura (POST, PUT, PATCH, DELETE) requiere autenticación; la lectura es pública.

| Recurso | Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
|---|---|---|---|---|
| Examen | `/api/exams/` | GET | — | 200, `{count, next, previous, results:[…]}` |
| Examen | `/api/exams/` | POST | `{"title":"Redes","description":"Quiz"}` | 201, examen con `id`, `created_at`, `question_count` |
| Examen | `/api/exams/{id}/` | GET | — | 200, objeto examen (404 si no existe) |
| Examen | `/api/exams/{id}/` | PUT | `{"title":"Redes II","description":""}` | 200, examen actualizado |
| Examen | `/api/exams/{id}/` | PATCH | `{"title":"Redes II"}` | 200, examen actualizado |
| Examen | `/api/exams/{id}/` | DELETE | — | 204, sin cuerpo (borra sus preguntas) |
| Pregunta | `/api/questions/` | GET | — | 200, lista paginada; filtros `?exam=1`, `?search=texto`, `?page=2` |
| Pregunta | `/api/questions/` | POST | `{"exam":1,"text":"¿Verbo que crea?","points":2,"choices":[{"text":"POST","is_correct":true},{"text":"GET","is_correct":false}]}` | 201, pregunta con `choices` anidadas |
| Pregunta | `/api/questions/{id}/` | GET | — | 200, pregunta con `exam` (id) y `choices` |
| Pregunta | `/api/questions/{id}/` | PUT | cuerpo completo como en POST | 200 |
| Pregunta | `/api/questions/{id}/` | PATCH | `{"points":5}` | 200 |
| Pregunta | `/api/questions/{id}/` | DELETE | — | 204 |
| Opción | `/api/choices/` | GET | — | 200, lista paginada; filtros `?question=1`, `?search=texto` |
| Opción | `/api/choices/` | POST | `{"question":1,"text":"Otra","is_correct":false}` | 201, opción creada |
| Opción | `/api/choices/{id}/` | GET / PUT / PATCH / DELETE | `{"text":"Editada"}` (PATCH) | 200 / 200 / 200 / 204 |

> Nota: crear una opción suelta con `is_correct: true` en `/api/choices/` no re-valida la regla de «exactamente una correcta»; esa regla se aplica al crear o modificar la pregunta con sus opciones.

## Códigos de estado comprobados (pasos 7 a 9, cliente externo)

Salida real de `scripts/http_client_check.py` contra el servidor en marcha:

| Operación | Código |
|---|---|
| GET `/exams/` (lista) | 200 |
| GET `/exams/1/` (detalle) | 200 |
| POST `/questions/` (crear) | 201 |
| PATCH `/questions/{id}/` | 200 |
| DELETE `/questions/{id}/` | 204 |
| POST `/exams/` sin `title` | 400 `{"title":["This field is required."]}` |
| POST `/questions/` con `points:"many"` | 400 `{"points":["A valid integer is required."]}` |
| POST `/questions/` con 0 opciones correctas | 400 `{"choices":["La pregunta debe tener exactamente una opcion correcta (recibidas: 0)."]}` |
| POST `/questions/` con 2 opciones correctas | 400 (recibidas: 2) |
| POST `/exams/` sin credenciales | 403 `Authentication credentials were not provided.` |
| GET `/exams/9999/` | 404 |
| GET `/questions/?page=2` (7 preguntas, página de 5) | 200, 2 resultados, `previous` apunta a la página 1 |

## Pendiente del alumno

Las capturas de la API navegable y de la estructura del proyecto en VS Code, y la sección de «Conclusiones» del entregable, dependen de tu ejecución local. Falta también subir el proyecto al repositorio del equipo y el entregable al campus virtual.
