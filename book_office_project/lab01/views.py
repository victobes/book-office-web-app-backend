from django.shortcuts import render

MINIO_HOST = "localhost"
MINIO_PORT = 9000
MINIO_DIR = "book-office-services-images"
EXTENSION = ".jpg"

services = [
    {
        "id": 1,
        "title": "Корректура текста",
        "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/1{EXTENSION}',
        "price": "от 45 руб. за 1000 символов",
        "description": "Корректура текста (корректорская правка) - это исправление орфографических, грамматических и пунктуационных ошибок в тексте, устранение морфологических ошибок (употребления форм склонения, числа, падежа и т.д.), проверку соблюдения правил переноса.",
    },
    {
        "id": 2,
        "title": "Дизайн обложки",
        "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/2{EXTENSION}',
        "price": "от 3500 руб.",
        "description": "Разрабатываем дизайн обложки для книги любого жанра.\nСложность: от простой шрифтовой композиции до сложной иллюстрированной.\nТехнические требования: для книг в разных переплетах.\nВыбор: всегда предоставляем три варианта дизайна на выбор заказчику.\nИспользуем лицензионные шрифты и картинки, учитываем пожелания.",
    },
    {
        "id": 3,
        "title": "Вёрстка книги",
        "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/3{EXTENSION}',
        "price": "от 65 руб. за 1 страницу",
        "description": "Верстаем книги любой сложности и любого формата.\nМакеты: полиграфический и электронный.\nСложность: от художественной литературы до научной с формулами.\nДизайн: от незамысловатого до макета с разработанной дизайн-концепцией.\nСоблюдаем технические требования типографии, СанПины и ГОСТы.",
    },
    {
        "id": 4,
        "title": "Иллюстрирование",
        "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/4{EXTENSION}',
        "price": "от 1200 руб.",
        "description": "Работаем с иллюстративным материалом для книги.\nОтрисовка: создаем иллюстрации с нуля по вашему техническому заданию или составляем ТЗ. В разных стилях и техниках.\nПодбор: подбираем иллюстрации из лицензионных стоков под вашу тематику в едином стиле.",
    },
]

orders = [
    {
        "id": 1,
        "format": "A4",
        "circulation": 500,
        "selected_services": [
            {
                "id": 2,
                "title": "Дизайн обложки",
                "price": "от 3500 руб.",
                "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/2{EXTENSION}',
                "rate": 'Тариф "Базовый"',
            },
            {
                "id": 3,
                "title": "Вёрстка книги",
                "price": "от 65 руб. за 1 страницу",
                "service_img_src": f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/3{EXTENSION}',
                "rate": 'Тариф "Базовый"',
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
                "rate": 'Тариф "Базовый"',
            },
            {
                "id": 4,
                "title": "Иллюстрирование",
                "price": "от 1200 руб.",
                "rate": 'Тариф "Премиум"',
            },
            {
                "id": 1,
                "title": "Корректура текста",
                "price": "от 45 руб. за 1000 символов",
                "rate": 'Тариф "Базовый"',
            },
        ],
    },
]

def get_services_list(search_query: str):
    result = []
    for service in services:
        if service["title"].lower().startswith(search_query.lower()):
            result.append(service)
            # result[-1][
            #     "service_img_src"
            # ] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{service["id"]}{EXTENSION}'
    return result


def get_services_list_page(request):
    search_query = request.GET.get("search_query", "")
    current_order_id = 1

    return render(
        request,
        "services.html",
        {
            "data": {
                "services": get_services_list(search_query),
                "count": len(orders[current_order_id - 1]["selected_services"]),
                "order_id": current_order_id,
            },
        },
    )


def get_service_page(request, id):
    for service in services:
        if service["id"] == id:
            # service["service_img_src"] = (
            #     f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{service["id"]}{EXTENSION}'
            # )
            return render(request, "service.html", {"data": service})
    render(request, "service.html")

# def get_service_info_by_id(id):
#     for service in services:
#         if service['id'] == id:
#             return service
        
# def add_services_info(services_list):
#     for service in services_list:
#         if service['id'] in id_list:
#             service['service_img_src'] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{service["id"]}{EXTENSION}'
#             selected_services.append(service)
#     return selected_services

def get_order_page(request, id):
    id = 1
    for order in orders:
        if order["id"] == id:
            return render(
                request,
                "order.html",
                {
                    "data": {
                        "id": id,
                        "format": order["format"],
                        "circulation": order["circulation"],
                        "services": order["selected_services"],
                    },
                },
            )


# def get_order_page(request, id):
#     id = 1
#     return render(
#         request,
#         "order.html",
#         {"data": get_order_data(id)},
#     )


# def order_page(request, id):
#     if id != 0:
#         return render(request, "order.html")

#     return render(request, "order.html", {"data": get_order_data()})

# def get_order_data(id):
#     for order in orders:
#         if order["id"] == id:
#             current_order = order.copy()
#     selected_services_count = len(current_order["selected_services"])
#     for service in current_order['selected_services']:
#         service[
#             "service_img_src"
#         ] = f'http://{MINIO_HOST}:{MINIO_PORT}/{MINIO_DIR}/{service["id"]}{EXTENSION}'
#         service_id = service['id']
#         service = services[]
#     return {
#         "order": current_order,
#         "selected_services_count": selected_services_count,
#     }
