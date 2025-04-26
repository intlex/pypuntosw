## PyPuntoSw

Анализирует и преобразует выделенный текст в нужную раскладку клавиатуры.
Поддерживается преобразование между русским и английским языком.

# Installation
```
pip install pyenchant pymorphy3 pymorphy3-dicts-ru
apt-get install -y libenchant-2-2 hunspell-ru
wget https://github.com/intlex/pypuntosw/raw/refs/heads/main/translit.py
```
Чтобы не устанавливать ненужные зависимости, лучше всего скачать `pynput` отдельно https://github.com/moses-palmer/pynput
При необходимости измените в файле `translit.py` коды клавиш у `GlobalHotKeys` на предпочтительные.

# Usage

* Запустить скрипт после установки всех зависимостей
  `python3 translit.py`
* Выделить текст, например:
  `если rjl c nfrbvb bvgjhnfvb? шьфпуышяу ,eltn kb jy hf,jnfnm gjl fylhjbl ХсдшзЪ <kjr123 привет fryiend`
* Нажать кнопку `Pause`, текст будет заменен на:
  `если код c такими импортами, imagesize будет ли он работать под андроид {clip} Блок123 привет fryiend`
* Нажать сочетание клавиш `Shift + Pause` для для принудительной смены раскладки.

# Notice

При необходимости можете добавить свои кодировочные таблицы для требуемого языка.
Так же можно доработать функцию `is_word_recognized_advanced`, а для функции `process_text` использовать библиотеку `langid` для поддержки разных языков.
