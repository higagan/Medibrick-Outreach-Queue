from bs4 import BeautifulSoup

with open('indeed_full.html', 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find all elements containing date text
count = 0
for elem in soup.find_all(text=lambda t: t and ('days ago' in t or 'Today' in t or 'hours ago' in t)):
    parent = elem.parent
    print('TEXT:', repr(elem.strip()))
    print('TAG:', parent.name if parent else 'NONE')
    print('CLASS:', parent.get('class') if parent else 'NONE')
    print('---')
    count += 1
    if count >= 5:
        break

print(f"\nTotal date elements found: {count}")
