## Сравнение XML с маршрутами via.com

Скрипт выводит разницу между XML-файлами с информацией о маршрутах via.com.

### Запуск

Для запуска требуется установленный python3.

В качестве аргументов нужно указать XML-файлы для сравнения. Если указан ключ `-ir`, совпадающими маршрутами считаются те, у которых номера рейсов одинаковы только в прямом направлении (onward).

Пример запуска:

```bash
python3 main.py RS_Via-3.xml RS_ViaOW.xml
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).





