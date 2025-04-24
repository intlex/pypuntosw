## PyPuntoSw

Анализирует и преобразует выделенный текст в нужную раскладку клавиатуры.
Поддерживается преобразование между русским и английским языком.

# Installation
```
pip install pyenchant pymorphy3 pymorphy3-dicts-ru
apt-get install -y libenchant-2-2 hunspell-ru
```

# Usage

* Запустить скрипт после установки всех зависимостей
  `python3 translit.py`
* Выделить текст, например:
  `tcnm rjl c nfrbvb bvgjhnfvb? шьфпуышяу ,eltn kb jy hf,jnfnm gjl fylhjbl ХсдшзЪ`
* Нажать кнопку `Pause`, текст будет заменен на:
  `есть код c такими импортами, imagesize будет ли он работать под андроид {clip}`

# Notice

При необходимости можете добавить свои кодировочные таблицы для требуемого языка.
Так же можно доработать функцию `is_word_recognized_advanced`, а для функции `process_text` использовать библиотеку `langid` для поддержки разных языков.
