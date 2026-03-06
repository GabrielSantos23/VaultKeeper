import codecs
import re
html = codecs.open('popup.html', 'r', 'utf-8').read()
js1 = codecs.open('popup.js', 'r', 'utf-8').read()
js2 = codecs.open('cards.js', 'r', 'utf-8').read()
js3 = codecs.open('notes.js', 'r', 'utf-8').read()

all_text = html + ' ' + js1 + ' ' + js2 + ' ' + js3
classes = re.findall(r'class(?:Name)?\s*=\s*[\'\"\`]([^\'\"\`]+)[\'\"\`]', all_text)
adds = re.findall(r'classList\.add\([\'\"\`]([^\'\"\`]+)[\'\"\`]', all_text)

all_classes = set()
for c in classes:
    for cls in c.split():
        all_classes.add(cls)

for c in adds:
    for cls in c.split():
        all_classes.add(cls)

out = ' '.join(all_classes)
codecs.open('test_classes.html', 'w', 'utf-8').write(f'<div class="{out}"></div>')
