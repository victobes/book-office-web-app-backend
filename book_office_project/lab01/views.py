from django.shortcuts import render

MINIO_HOST = "localhost"
MINIO_PORT = 9000
MINIO_DIR = "book-office-services-images"
EXTENSION = ".jpg"

book_production_services = [
    {
        "id": 1,
        "title": "Корректура текста",
        "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/1{EXTENSION}",
        "price": "от 45 руб. за 1000 символов",
        "description": "Корректура текста (корректорская правка) - это исправление орфографических, грамматических и пунктуационных ошибок в тексте, устранение морфологических ошибок (употребления форм склонения, числа, падежа и т.д.), проверку соблюдения правил переноса.",
    },
    {
        "id": 2,
        "title": "Дизайн обложки",
        "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/2{EXTENSION}",
        "price": "от 3500 руб.",
        "description": "Разрабатываем дизайн обложки для книги любого жанра.\nСложность: от простой шрифтовой композиции до сложной иллюстрированной.\nТехнические требования: для книг в разных переплетах.\nВыбор: всегда предоставляем три варианта дизайна на выбор заказчику.\nИспользуем лицензионные шрифты и картинки, учитываем пожелания.",
    },
    {
        "id": 3,
        "title": "Вёрстка книги",
        "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/3{EXTENSION}",
        "price": "от 65 руб. за 1 страницу",
        "description": "Верстаем книги любой сложности и любого формата.\nМакеты: полиграфический и электронный.\nСложность: от художественной литературы до научной с формулами.\nДизайн: от незамысловатого до макета с разработанной дизайн-концепцией.\nСоблюдаем технические требования типографии, СанПины и ГОСТы.",
    },
    {
        "id": 4,
        "title": "Иллюстрирование",
        "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/4{EXTENSION}",
        "price": "от 1200 руб.",
        "description": "Работаем с иллюстративным материалом для книги.\nОтрисовка: создаем иллюстрации с нуля по вашему техническому заданию или составляем ТЗ. В разных стилях и техниках.\nПодбор: подбираем иллюстрации из лицензионных стоков под вашу тематику в едином стиле.",
    },
]

book_publishing_projects = [
    {
        "id": 1,
        "format": "A4",
        "circulation": 500,
        "selected_services": [
            {
                "id": 2,
                "title": "Дизайн обложки",
                "price": "от 3500 руб.",
                "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/2{EXTENSION}",
                "rate": 'Тариф "Базовый"',
            },
            {
                "id": 3,
                "title": "Вёрстка книги",
                "price": "от 65 руб. за 1 страницу",
                "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/3{EXTENSION}",
                "rate": 'Тариф "Премиум"',
            },
        ],
    },
    {
        "id": 2,
        "format": "A5",
        "circulation": 10000,
        "selected_services": [
            {
                "id": 3,
                "title": "Вёрстка книги",
                "price": "от 65 руб. за 1 страницу",
                "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/3{EXTENSION}",
                "rate": 'Тариф "Базовый"',
            },
            {
                "id": 4,
                "title": "Иллюстрирование",
                "price": "от 1200 руб.",
                "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/4{EXTENSION}",
                "rate": 'Тариф "Премиум"',
            },
            {
                "id": 1,
                "title": "Корректура текста",
                "price": "от 45 руб. за 1000 символов",
                "service_img_src": f"http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/1{EXTENSION}",
                "rate": 'Тариф "Базовый"',
            },
        ],
    },
]


def get_book_production_services_list(search_query: str):
    result = []
    for service in book_production_services:
        if service["title"].lower().startswith(search_query.lower()):
            result.append(service)
    return result


def get_book_production_services_list_page(request):
    search_query = request.GET.get("book_production_service_name", "")
    current_project_id = 1

    return render(
        request,
        "book_production_services.html",
        {
            "data": {
                "services": get_book_production_services_list(search_query),
                "count": len(book_publishing_projects[current_project_id - 1]["selected_services"]),
                "project_id": current_project_id,
                "search_query": search_query,
            },
        },
    )


def get_book_production_service_page(request, id):
    for service in book_production_services:
        if service["id"] == id:
            return render(request, "book_production_service.html", {"data": service})
    render(request, "book_production_service.html")


def get_book_publishing_project_page(request, id):
    current_project_id = 1
    for project in book_publishing_projects:
        if project["id"] == current_project_id:
            return render(
                request,
                "book_publishing_project.html",
                {
                    "data": {
                        "id": current_project_id,
                        "format": project["format"],
                        "circulation": project["circulation"],
                        "services": project["selected_services"],
                    },
                },
            )
