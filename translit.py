import difflib
import re
import pymorphy3
import enchant
import pyclip
#import langid
# Инициализация словарей Enchant для английского и русского языков
try:
    eng_dict = enchant.Dict("en_US")
    rus_dict = enchant.Dict("ru_RU")
    #langid.set_languages(['ru', 'en'])
except Exception as e:
    raise Exception(f"{e}")
    
english_letters = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
# Таблицы соответствия символов.
RU_TO_EN = {
    'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y', 'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']', 
    'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h', 'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
    'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n', 'ь': 'm', 'б': ',', 'ю': '.', '.': '/',
    'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y', 'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '{', 'Ъ': '}',
    'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G', 'Р': 'H', 'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ':', 'Э': '"',
    'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V', 'И': 'B', 'Т': 'N', 'Ь': 'M', 'Б': '<', 'Ю': '>', ',': '?',
    '"': '@', '№': '#', ';': '$', ':': '^', '?': '&', 'ё': '`', 'Ё': '~'
}
# Обратная таблица
EN_TO_RU = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.',
    'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
    'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э',
    'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т', 'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',',
    '@': '"', '#': '№', '$': ';', '^': ':', '&': '?', '`': 'ё', '~': 'Ё'
}

merged_table = RU_TO_EN | EN_TO_RU;

def transliterate_using_table(word: str, mapping: dict) -> str:
    result = []
    for ch in word:
        if ch in mapping:
            result.append(mapping[ch])
        else:
            result.append(ch)
    return "".join(result)

def correct_fragment(fragment: str, lang: str, similarity_threshold) -> (bool, str, bool):
    lw = fragment.lower()
    # Если фрагмент напрямую распознан
    # или Собираем варианты исправления
    # Ненормальное распознавание Enchant однобуквенных слов
    # En: False-positive Enchant checks 1-letter words.
    sl_word = (len(fragment) == 1)
    #if sl_word:
    #    if 
    match lang:
        case 'en': 
            if sl_word:
                sl_word = lw in 'ia'
                return sl_word, fragment, sl_word
            else:
                if eng_dict.check(lw):
                    return True, fragment, True
                else:
                    suggestions = eng_dict.suggest(lw)
        case 'ru':  
            if sl_word:
                sl_word = lw in 'укваояси'
                return sl_word, fragment, sl_word
            else:
                if rus_dict.check(lw):
                    return True, fragment, True
                else:
                    suggestions = rus_dict.suggest(lw)
        case _:
            return False, fragment, False
    if not suggestions:
        return False, fragment, False  # Если вариантов нет, возвращаем исходный фрагмент
    best_suggestion = None
    best_score = 0.0
    for suggestion in suggestions:
        score = difflib.SequenceMatcher(None, lw, suggestion.lower()).ratio()
        if score > best_score:
            best_score = score
            best_suggestion = suggestion
    # Если найденный вариант достаточно похож, возвращаем его, иначе исходное слово
    if best_score >= similarity_threshold:
        return True, fragment, False #best_suggestion - из-за несовершенства словарей будем возвращать исходное
    else:
        return False, fragment, False

def is_word_recognized_advanced(word: str, lang: str, similarity_threshold=0.85) -> (bool, str, int):
    # Разбиваем слово на фрагменты. Фрагменты, состоящие из букв (латиница/русские буквы), и разделители
    fragments = re.split(r'([^A-Za-zА-Яа-яЁё]+)', word) #, flags=re.NOOP
    fragments = [item for item in fragments if item]
    if not fragments:
        return False, word, 0, False, 0

    recognized_any = False  # флаг, что хотя бы один буквенный фрагмент распознан или исправлен
    is_first = False
    weight =  0
    cnt = 1 
    corrected_fragments = []
    for frag in fragments:
        # Если в фрагменте есть буквы, обрабатываем отдельно
        if re.search(r'[A-Za-zА-Яа-яЁё]', frag.lower()):
            # Пробуем исправить фрагмент
            if not recognized_any:
                recognized, corrected, is_first = correct_fragment(frag, lang, similarity_threshold)
#            else:
#                corrected = frag
            weight = weight + (10 if is_first else 0)
            weight = weight + (1 if recognized else 0)
            print(f"{lang} {recognized}, {corrected}, {is_first}")
            # Если исправленный фрагмент проходит проверку, отмечаем, что фрагмент распознан
            if recognized:
                cnt = cnt + 1
            if recognized and is_first and (len(fragments) == 1):
                recognized_any = True
            corrected_fragments.append(corrected)
        else:
            # Если фрагмент не содержит букв (например, цифры, подчеркивания, пробелы) — оставляем как есть
            corrected_fragments.append(frag)
    corrected_word = "".join(corrected_fragments)
    weight = weight - len(fragments) + cnt
    return recognized_any, corrected_word, weight

#def recognize_word(word: str, lang: str) -> (bool, str, int, bool, int):
#    return is_word_recognized_advanced(word, lang)

#def process_pair(pair) -> (str, str):
#    word_en, word_ru = pair
#    check_en, word_en, cnt_en = recognize_word(word_en, 'en')
#    check_ru, word_ru, cnt_ru = recognize_word(word_ru, 'ru')
#    if check_en ^ check_ru:
#        result = word_en if check_en else word_ru
#    elif check_en and ((cnt_en == 1) ^ (cnt_ru == 1)):
#        result = word_en if cnt_en == 1 else word_ru
#    else:
#        result = (word_en, word_ru)
#    return result
    
def process_word(word: str, lang: str) -> (bool, int):
    check, word, weight = is_word_recognized_advanced(word, lang)
    print(f"{word}: {check}, {weight}")
    return check, weight

def simple_process_text(input_text: str) -> str:
    return transliterate_using_table(input_text, merged_table);

def process_text(input_text: str) -> str: #(str, str):
    # Проверяем как есть, если не помогло - перекодируем и снова проверяем
    words = input_text.split()
    word_pairs = []
    for word in words:
        # определяем язык
        #lang, confidence = langid.classify(word)
        #match lang:
        #    case 'en':
        #    case 'ru':
        if re.search(r'[а-яА-Я]', word):
            word_r = word
            check_r, weight_r = process_word(word_r, 'ru')
            if check_r:
                word_pairs.append(word_r)
            else:
                word_e = transliterate_using_table(word_r, RU_TO_EN)
                check_e, weight_e = process_word(word_e, 'en')
                if check_e:
                    word_pairs.append(word_e)
                else:
                    if weight_e == weight_r:
                        word_pairs.append((word_e, word_r))
                    else:
                        word_pairs.append(word_e if weight_e > weight_r else word_r)
        else:
            word_e = word
            check_e, weight_e = process_word(word_e, 'en')
            if check_e:
                word_pairs.append(word_e)
            else:
                word_r = transliterate_using_table(word, EN_TO_RU)
                check_r, weight_r = process_word(word_r, 'ru')
                if check_r:
                    word_pairs.append(word_r)
                else:
                    if weight_e == weight_r:
                        word_pairs.append((word_e, word_r))
                    else:
                        word_pairs.append(word_e if weight_e > weight_r else word_r)

    words = word_pairs    
    # Следующий вариант не годится, если встречается нормальное слово со знаками препинания в конце
    # когда сразу Перекодируем строку в оба варианта, быстрее чем определять язык
    #str_ru = transliterate_using_table(input_text, EN_TO_RU)
    #words_ru = str_ru.split()
    #str_en = transliterate_using_table(input_text, RU_TO_EN)
    #words_en = str_en.split()
    # Объединяем в набор пар слов в одной и другой раскладке    
    #word_pairs = list(zip(words_en, words_ru))
    # Меняем местами слова в парах, чтобы первым шло английское слово
    # и отдаем на распознавание 
    #print(word_pairs)
    #words = []
    #for i in range(len(word_pairs)):
    #    word1, word2 = word_pairs[i]
    #    if re.match(r'[а-яА-Я]', word1):
    #        word_pairs[i] = (word2, word1)
    #    words.append(process_pair(word_pairs[i]))
    
    # Подсчитаем сколько слов каждого алфавита, чтобы определить язык всей строки
    # todo: надо бы исключать из подсчета числа
    words_en = 0
    words_ru = 0        
    #print(words)
    for word in words:
        if isinstance(word, tuple):
            continue  # Игнорируем слова в кортежах
        else:
            if any(char in english_letters for char in word):
                words_en += 1
            else:
                words_ru += 1
    index = 0 if words_en >= words_ru else 1;
    for i in range(len(words)):
        if isinstance(words[i], tuple):
            words[i] = words[i][index]
    return " ".join(words) #lang to switch

import pynput
from pynput.keyboard import Key, Controller
#import keyboard
from time import sleep

def intelligence_handler(): #event):
    try:
        keyboard = Controller()
        # copy некорректно работает с двоичными данными, превращает их в строку
        # поэтому принудительно ставим ставим флаг text для сохранения текстового буфера
        # возможно кодирование в base64 может помочь
        old_clip_data = pyclip.paste(text=True)
        sleep(0.3)
        with keyboard.pressed(Key.ctrl):
            keyboard.press('c')
            keyboard.release('c')
        #keyboard.press_and_release('ctrl+c')
        sleep(0.1)
        input_text = pyclip.paste(text=True)
        result_text = process_text(input_text)
        pyclip.copy(result_text)
        sleep(0.1)
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        #keyboard.press_and_release('ctrl+v')
        print("Результат:", result_text)
        sleep(0.3)
        pyclip.copy(old_clip_data) #.decode('utf-8')
        # надо сменить раскладку на основной язык корректно
        #keyboard.press(Key.cmd)
        #sleep(0.1)
        #keyboard.release(Key.cmd)
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def simple_handler(): #event):
    try:
        keyboard = Controller()
        old_clip_data = pyclip.paste(text=True)
        sleep(0.3)
        with keyboard.pressed(Key.ctrl):
            keyboard.press('c')
            keyboard.release('c')
        #keyboard.press_and_release('ctrl+c')
        sleep(0.1)
        input_text = pyclip.paste(text=True)
        result_text = simple_process_text(input_text)
        pyclip.copy(result_text)
        sleep(0.1)
        with keyboard.pressed(Key.ctrl):
            keyboard.press('v')
            keyboard.release('v')
        #keyboard.press_and_release('ctrl+v')
        print("Результат:", result_text)
        sleep(0.3)
        pyclip.copy(old_clip_data) #.decode('utf-8')
    except Exception as e:
        print(f"Произошла ошибка: {e}")

if __name__ == "__main__":
    with pynput.keyboard.GlobalHotKeys({
            '<shift>+<pause>': simple_handler,
            '<pause>': intelligence_handler}) as h:
        h.join()
    #keyboard.on_press_key('<pause>', intelligence_handler)
    #keyboard.on_press_key('<shift>+<pause>', simple_handler)
    #keyboard.wait('ctrl+alt+esc')
    #exit()
    #input_text = "-ды"
    #'tcnm rjl c nfrbvb bvgjhnfvb? шьфпуышяу ,eltn kb jy hf,jnfnm gjl fylhjbl ХсдшзЪ <kjr123 привет fryiend'
    #input_text = "<kjr123 шьфпу_ышяу привет fryiend ашдуюшьп ,ehfnbyj"
    #result_text = process_text(input_text)
    #pyclip.copy(result_text)
    #print("Результат:", result_text)
