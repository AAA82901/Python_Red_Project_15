## Ошибки, обрабатываемые сервисом
1) Ошибка подключения (requests.exceptions.ConnectionError),
возникающая, например, при отсутствии подключения к интернету на устройстве. Определяются с помощью конструкции try-except.
2) Любые другие ошибки. Определяются с помощью проверки кода ответа на запрос.

## Некорректные данные, которые может ввести пользователь, но которые сервис обрабатывает корректно
1) Пустое поле для названия (начала названия) пункта отправления или прибытия.
Способ обработки: у пользователя нет возможности ввести данные,
пока поле для названия (начала названия) пункта отправления или 
поле для названия (начала названия) пункта прибытия
пустое.
2) Иным образом некорректное название (начало названия) пункта отправления или прибытия.
Способ обработки: отображение страницы с информацией о некорректности данных.
2) Совпадающие пункты: отправления и прибытия.
Способ обработки: отображение страницы с информацией о некорректности данных.