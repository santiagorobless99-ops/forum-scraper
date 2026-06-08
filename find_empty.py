import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BOARD_PATTERN = re.compile(r'Rozed\s*/([^\n]+)', re.IGNORECASE)
HEADER_TAGS   = re.compile(r'^(?:SEG|FAV|HIDE|DENUNCIAR|FOLLOW|COMPARTIR)\s*\n', re.MULTILINE)
TIMESTAMP     = re.compile(r'^\d+[\s]*(s|m|h|d|sem|min|seg|hr?s?)\b.*\n', re.MULTILINE)
HTML_TAGS     = re.compile(r'<[^>]+>')
QUOTE_SEP     = re.compile(r'>>(\w+)')


def clean_text(text):
    text = HTML_TAGS.sub('', text)
    text = BOARD_PATTERN.sub('', text)
    text = HEADER_TAGS.sub('', text)
    text = TIMESTAMP.sub('', text)
    text = QUOTE_SEP.sub(r'@\1', text)
    text = text.strip()
    text = text.replace('\n', ' | ')
    text = re.sub(r'(\s*\|\s*){2,}', ' | ', text)
    return text


data = json.load(open('rozed_dataset_masivo.json', encoding='utf-8'))

for thread in data:
    for idx, msg in enumerate(thread.get('contenido', [])):
        cleaned = clean_text(msg)
        if cleaned.strip() == '':
            thread_id = thread['id']
            url       = thread['url']
            msg_count = len(thread['contenido'])
            images    = thread.get('imagenes', [])
            print('=== EMPTY MESSAGE FOUND ===')
            print(f'Thread ID   : {thread_id}')
            print(f'URL         : {url}')
            print(f'Position    : message {idx+1} of {msg_count}')
            print(f'Is OP       : {"Yes" if idx==0 else "No"}')
            print(f'Raw content : {repr(msg)}')
            print(f'Raw length  : {len(msg)} characters')
            print(f'Images      : {images}')
            print()
