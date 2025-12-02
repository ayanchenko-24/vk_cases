
import json
from bs4 import BeautifulSoup
import os


def main():
    print("=" * 60)
    print("ПАРСЕР КЕЙСОВ VK - НАЧАЛО РАБОТЫ")
    print("=" * 60)
    
    # 1. Проверяем, есть ли сохраненная страница
    html_files = ['page.html', 'vk_cases.html', 'cases.html']
    html_file = None
    
    for file in html_files:
        if os.path.exists(file):
            html_file = file
            print(f"✓ Найден файл: {file}")
            break
    
    if not html_file:
        print("\n❌ ОШИБКА: Не найден HTML-файл!")
        print("\nВам нужно:")
        print("1. Открыть https://ads.vk.com/cases в браузере")
        print("2. Нажать Ctrl+S (сохранить)")
        print("3. Сохранить как 'page.html' в эту папку")
        print("4. Выбрать 'Веб-страница, полностью'")
        return
    
    # 2. Читаем файл
    print(f"\n📖 Читаю файл {html_file}...")
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print("✓ Файл успешно прочитан")
    except:
        print("⚠️ Пробую другую кодировку...")
        with open(html_file, 'r', encoding='cp1251') as f:
            html_content = f.read()
        print("✓ Файл прочитан (кодировка cp1251)")
    
    # 3. Парсим HTML
    print("\n🔍 Начинаю парсинг...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 4. Ищем карточки разными способами
    print("\n👀 Ищу карточки на странице...")
    
    # Список всех возможных вариантов
    all_cards = []
    
    # Вариант 1: Ищем по тегу <article>
    articles = soup.find_all('article')
    print(f"Найдено <article>: {len(articles)}")
    all_cards.extend(articles)
    
    # Вариант 2: Ищем div с классами, содержащими "case" или "card"
    all_divs = soup.find_all('div')
    for div in all_divs:
        if div.get('class'):
            classes = ' '.join(div.get('class')).lower()
            if 'case' in classes or 'card' in classes:
                all_cards.append(div)
    
    print(f"Найдено div с case/card: {len([c for c in all_divs if 'case' in str(c.get('class', '')).lower() or 'card' in str(c.get('class', '')).lower()])}")
    
    # Убираем дубликаты
    unique_cards = []
    seen = set()
    for card in all_cards:
        card_str = str(card)[:100]  # Берем первые 100 символов для сравнения
        if card_str not in seen:
            seen.add(card_str)
            unique_cards.append(card)
    
    print(f"\n📊 Всего уникальных карточек найдено: {len(unique_cards)}")
    
    if len(unique_cards) == 0:
        print("\n⚠️ Карточки не найдены стандартными методами")
        print("Пробую расширенный поиск...")
        
        # Ищем любой контент, похожий на карточку
        for tag in soup.find_all(['div', 'section', 'li', 'a']):
            text = tag.text.strip()
            # Если есть достаточно текста и нет лишних тегов
            if len(text) > 20 and len(text) < 500:
                if tag not in unique_cards:
                    unique_cards.append(tag)
        
        print(f"Найдено потенциальных элементов: {len(unique_cards)}")
    
    # 5. Извлекаем данные из карточек
    print("\n📝 Извлекаю данные...")
    cases = []
    
    for i, card in enumerate(unique_cards[:50]):  # Обрабатываем первые 50
        try:
            case_data = {}
            
            # Название (ищем заголовки)
            title = None
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                title_elem = card.find(tag)
                if title_elem and title_elem.text.strip():
                    title = title_elem.text.strip()
                    break
            
            # Если не нашли заголовок, берем первый текст
            if not title:
                all_text = card.text.strip().split('\n')
                for text in all_text:
                    if text.strip() and len(text.strip()) > 10:
                        title = text.strip()[:100]  # Берем первые 100 символов
                        break
            
            if not title:
                continue  # Пропускаем если нет названия
            
            case_data['title'] = title
            
            # Ссылка
            link = None
            link_elem = card.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                # Делаем ссылку абсолютной
                if href.startswith('/'):
                    link = 'https://ads.vk.com' + href
                elif href.startswith('http'):
                    link = href
                else:
                    link = 'https://ads.vk.com/' + href
            
            case_data['link'] = link if link else "Ссылка не найдена"
            
            # Дата
            date = None
            # Ищем тег time
            time_elem = card.find('time')
            if time_elem:
                date = time_elem.text.strip()
                if time_elem.get('datetime'):
                    date = time_elem['datetime']
            
            # Ищем дату в тексте
            if not date:
                import re
                date_patterns = [
                    r'\d{2}\.\d{2}\.\d{4}',  # 01.01.2024
                    r'\d{4}-\d{2}-\d{2}',     # 2024-01-01
                    r'\d{1,2}\s+\w+\s+\d{4}', # 1 января 2024
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, card.text)
                    if matches:
                        date = matches[0]
                        break
            
            case_data['date'] = date if date else "Дата не указана"
            
            # Добавляем кейс
            cases.append(case_data)
            print(f"  ✓ Обработан кейс {i+1}: {title[:50]}...")
            
        except Exception as e:
            print(f"  ✗ Ошибка в карточке {i+1}: {str(e)[:50]}")
            continue
    
    # 6. Сохраняем результаты
    print(f"\n💾 Сохраняю результаты...")
    
    if cases:
        # Сохраняем в JSON
        with open('vk_cases.json', 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"✓ Сохранено в vk_cases.json ({len(cases)} кейсов)")
        
        # Сохраняем в текстовый файл
        with open('vk_cases.txt', 'w', encoding='utf-8') as f:
            f.write(f"Всего найдено кейсов: {len(cases)}\n")
            f.write("=" * 60 + "\n\n")
            for i, case in enumerate(cases, 1):
                f.write(f"КЕЙС #{i}\n")
                f.write(f"Название: {case['title']}\n")
                f.write(f"Ссылка: {case['link']}\n")
                f.write(f"Дата: {case['date']}\n")
                f.write("-" * 40 + "\n\n")
        print(f"✓ Сохранено в vk_cases.txt")
        
        # Показываем результат в консоли
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ ПАРСИНГА")
        print("=" * 60)
        for i, case in enumerate(cases[:5], 1):  # Показываем первые 5
            print(f"\n{i}. {case['title'][:70]}...")
            print(f"   📎 {case['link'][:50]}..." if len(case['link']) > 50 else f"   📎 {case['link']}")
            print(f"   📅 {case['date']}")
        
        if len(cases) > 5:
            print(f"\n... и еще {len(cases) - 5} кейсов")
            
    else:
        print("\n😞 К сожалению, не найдено ни одного кейса")
        print("Вероятные причины:")
        print("1. Структура страницы нестандартная")
        print("2. Нужно сохранить страницу по-другому")
        print("\nПопробуйте:")
        print("1. Пересохранить страницу")
        print("2. Проверить файл page.html в текстовом редакторе")
    
    print("\n" + "=" * 60)
    print("РАБОТА ЗАВЕРШЕНА")
    print("=" * 60)
    print("\nНажмите Enter чтобы выйти...")
    input()


if __name__ == "__main__":
    main()