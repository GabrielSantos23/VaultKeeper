import codecs
import re

html = codecs.open('popup.html', 'r', 'utf-8').read()
js1 = codecs.open('popup.js', 'r', 'utf-8').read()
js2 = codecs.open('cards.js', 'r', 'utf-8').read()
js3 = codecs.open('notes.js', 'r', 'utf-8').read()

all_text = html + " " + js1 + " " + js2 + " " + js3
# regex to find all class="..." and className="..." and classList.add("...")
classes_list = []
matches = re.findall(r'class="([^"]+)"', all_text)
classes_list.extend(matches)
matches2 = re.findall(r'className\s*=\s*(?:[`"\'])(.*?)(?:[`"\'])', all_text, re.DOTALL)
classes_list.extend(matches2)
matches3 = re.findall(r'classList\.add\("([^"]+)"\)', all_text)
classes_list.extend(matches3)
matches4 = re.findall(r'classList\.add\(\'([^\']+)\'\)', all_text)
classes_list.extend(matches4)

all_classes = set()
for c in classes_list:
    c = c.replace('\\n', ' ').replace(';', ' ') # clean up
    for cls in c.split():
        if cls and len(cls) > 1 and not cls.startswith('('):
            all_classes.add(cls)

out = ' '.join(all_classes)
codecs.open('test_classes.html', 'w', 'utf-8').write(f'<div class="{out}"></div>')
