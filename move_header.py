import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

header_pattern = re.compile(r'(        <!-- Header Frame -->\n        <div class="header-frame">.*?</div>\n)', re.DOTALL)
match = header_pattern.search(html)

if match:
    header_html = match.group(1)
    # Remove header from blueprint-container
    html = html.replace(header_html, '')
    # Adjust margin-bottom of header to 24px maybe?
    header_html = header_html.replace('margin-bottom: 8px;', 'margin-bottom: 24px;')
    # Insert before main-layout
    html = html.replace('<body>\n    <div class="main-layout">', f'<body>\n{header_html}    <div class="main-layout">')

    # I'll also add a class wrapper if needed, but it should be fine. Wait, let me adjust the margin via regex or just replace.
    # Ah wait, I can just write it directly.
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Success")
else:
    print("Not found")
