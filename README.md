# sqlbehave

Testing SQL by BDD method.

Установка осуществляется из pypi-репозитория:
```bash
pip install sqlbehave
```

После установки будет доступен скрипт для управления sqlbehave проектами `sqlbehave-admin.py`. Также он формирует python-скрипты для behave из файлов `.sql`, которые являются тестами.

Для того, чтобы начать проект создайте директорию проекта и настройте подключение к серверу(-ам):
```bash
mkdir AdWorks
cd AdWorks

cat >> settings.py
link_config = {
  'adworks': "mssql+pymssql://login:password@mssqlserver/AdventureWorks",
}
```

Весь код разбивается на модули. Чтобы создать новый модуль выполните команды:
```bash
sqlbehave-admin.py startmodule -m NewModule
cd NewModule
```

Далее можно приступать к написанию feature-файлов и их реализации в директории `steps` в файлах с расширением `.sql`.
Например, простой тест калькулятора будет выглядеть следующим образом:
```bash
cd features

cat >> calc.feature
Scenario: Сложение двух целых чисел
Given Значение х = 2
And Значение y = 2
When Вызывается процедура test.binary_sum с результатом z
Then Результат z = 4
```

Реализация тестов выполняется в файлах `.sql`.
Предикаты "Given Значение х = 2":
```bash
cat >> steps/"given Значение {var} = {value}.sql"
--!connect=adworks
--линк из settings.py

IF @context IS NULL
	SET @context = '<context />'

SET @context.modify('insert <alias></alias> as first into (/context[1])')
SET @context.modify('insert attribute name {sql:variable("@var")} into (/context[1]/alias[1])')
SET @context.modify('insert attribute value {sql:variable("@value")} into (/context[1]/alias[1])')
```

Предикат "When Вызывается процедура test.binary_sum с результатом z":
```bash
cat >> steps/"when Вызывается процедура test.binary_sum с результатом {var}.sql"
--!connect=adworks

DECLARE @x INT,
        @y INT,
        @z INT
        
SELECT @x = @context.value('/context[1]/alias[@name="x"][1]/@value[1]', 'INT')
SELECT @y = @context.value('/context[1]/alias[@name="y"][1]/@value[1]', 'INT')

EXEC test.binary_sum
  @x = @x,
  @y = @y,
  @z = @z OUTPUT

SET @context.modify('insert <alias></alias> as first into (/context[1])')
SET @context.modify('insert attribute name {sql:variable("@var")} into (/context[1]/alias[1])')
SET @context.modify('insert attribute value {sql:variable("@z")} into (/context[1]/alias[1])')

```

Предикат "Then Результат z = 4":
```bash
cat >> steps/"Then Результат {var} = {val}.sql"
--!connect=adworks

DECLARE @z INT,
        @res INT
        
SELECT @res = CAST(@val AS INT)
SELECT @z = @context.value('/context[1]/alias[@name=sql:variable("@var")][1]/@value[1]', 'INT')

IF @z != @res
  RAISERROR('Ошибка в сложении!', 16, 1);

```
При выполнении кода будут доступы дополнительные переменные:
* `@context XML` - содержит данные контекста, которые отображены в виде XML. Используется для передачи информации от одних предикатов к другим предикатам и имеет произвольную форму, которая определяется нуждами автора тестов.
* `@table XML` - содержит XML-представление таблицы после объявления предиката. Таблица для данного предиката будет выглядеть следующим образом:
```xml
<context>
    <table>
        <!-- param_name - наименование столбца; param_value - значение в столбце -->
        <row param_name="custom_field" param_value="3">
        <row param_name="other_field" param_value="Тестовая запись">
        <!-- и так далее... -->
    </table>
</context>
```

В случае критической ошибки будет произведён откат только текущего шага!

Для того, чтобы сформировать python-скрипты для исполнения тестов выполните команду:
```bash
# создаст файлы environment.py и NewModule.py, в которых происходит исполнение sql на MSSQL-сервере
sqlbehave-admin.py mksteps

# запуск сценариев тестирования
cd NewModule
behave
```
