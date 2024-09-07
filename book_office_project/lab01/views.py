from django.shortcuts import render

services = [
    {
        'id': 1, 
        'title': 'Корректура текста', 
        'price': 'от 45 руб. за 1000 символов', 
        'description': 'Корректура текста (корректорская правка) - это исправление орфографических, грамматических и пунктуационных ошибок в тексте, устранение морфологических ошибок (употребления форм склонения, числа, падежа и т.д.), проверку соблюдения правил переноса.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
    {
        'id': 2, 
        'title': 'Дизайн обложки', 
        'price': 'от 3500 руб.', 
        'description': 'Разрабатываем дизайн обложки для книги любого жанра.\nСложность: от простой шрифтовой композиции до сложной иллюстрированной.\nТехнические требования: для книг в разных переплетах.\nВыбор: всегда предоставляем три варианта дизайна на выбор заказчику.\nИспользуем лицензионные шрифты и картинки, учитываем пожелания.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
    {
        'id': 3, 
        'title': 'Вёрстка книги', 
        'price': 'от 65 руб. за 1 страницу', 
        'description': 'Верстаем книги любой сложности и любого формата.\nМакеты: полиграфический и электронный.\nСложность: от художественной литературы до научной с формулами.\nДизайн: от незамысловатого до макета с разработанной дизайн-концепцией.\nСоблюдаем технические требования типографии, СанПины и ГОСТы.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
    {
        'id': 4, 
        'title': 'Иллюстрирование', 
        'price': 'от 1200 руб.', 
        'description': 'Работаем с иллюстративным материалом для книги.\nОтрисовка: создаем иллюстрации с нуля по вашему техническому заданию или составляем ТЗ. В разных стилях и техниках.\nПодбор: подбираем иллюстрации из лицензионных стоков под вашу тематику в едином стиле.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
]

orders = [
    {
    'id':1,
    'format': 'A4',
    'circulation': 500,
    'selected_services': [
    {
        'id': 2, 
        'title': 'Дизайн обложки', 
        'price': 'от 3500 руб.', 
        'description': 'Разрабатываем дизайн обложки для книги любого жанра. Сложность: от простой шрифтовой композиции до сложной иллюстрированной. Технические требования: для книг в разных переплетах. Выбор: всегда предоставляем три варианта дизайна на выбор заказчику. Используем лицензионные шрифты и картинки, учитываем пожелания.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
    {
        'id': 3, 
        'title': 'Вёрстка книги', 
        'price': 'от 65 руб. за 1 страницу', 
        'description': 'Верстаем книги любой сложности и любого формата. Макеты: полиграфический и электронный. Сложность: от художественной литературы до научной с формулами. Дизайн: от незамысловатого до макета с разработанной дизайн-концепцией. Соблюдаем технические требования типографии, СанПины и ГОСТы.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png'
    },
    ]
    },
    {
    'id':2,
    'format': 'A5',
    'circulation': 10000,
    'selected_services': [
    {
        'id': 3, 
        'title': 'Вёрстка книги', 
        'price': 'от 65 руб. за 1 страницу', 
        'description': 'Верстаем книги любой сложности и любого формата.\nМакеты: полиграфический и электронный.\nСложность: от художественной литературы до научной с формулами.\nДизайн: от незамысловатого до макета с разработанной дизайн-концепцией.\nСоблюдаем технические требования типографии, СанПины и ГОСТы.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png',
        'rate': 'Тариф "Базовый"',
    },
    {
        'id': 4, 
        'title': 'Иллюстрирование', 
        'price': 'от 1200 руб.', 
        'description': 'Работаем с иллюстративным материалом для книги.\nОтрисовка: создаем иллюстрации с нуля по вашему техническому заданию или составляем ТЗ. В разных стилях и техниках.\nПодбор: подбираем иллюстрации из лицензионных стоков под вашу тематику в едином стиле.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png',
        'rate': 'Тариф "Премиум"',
    },
    {
        'id': 1, 
        'title': 'Корректура текста', 
        'price': 'от 45 руб. за 1000 символов', 
        'description': 'Корректура текста (корректорская правка) - это исправление орфографических, грамматических и пунктуационных ошибок в тексте, устранение морфологических ошибок (употребления форм склонения, числа, падежа и т.д.), проверку соблюдения правил переноса.', 
        'image': 'http://172.19.0.3:9000/server-soft-logos/logo-docker.png',
        'rate': 'Тариф "Базовый"',
    },
    ]
    },
]

def get_services_list_page(request):
    input_text = ""
    return render(request, 'index.html',
                  {'data': {
                      'services': [i for i in services if i["title"].startswith(input_text)],
                      'count': len(orders[1]['selected_services'])
                  },})

def get_service_page(request, id):
    for i in services:
        if i['id'] == id:
            return render(request, 'service.html',
                          {'data': i})
    render(request, 'service.html')
    
    
def get_order_page(request, id):
    for order in orders:
        if order['id'] == id:
            return render(request, 'order.html',
                          {'data': {
                            'id': id,
                            'format': order['format'],
                            'circulation': order['circulation'],
                            'services': order['selected_services']  
                          },})
    # if id != 0:
    #     return render(request, 'order.html')

    # return render(request, 'order.html',
    #               {'data': orders[1]})