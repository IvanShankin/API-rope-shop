"""Fill every admin text slot from the site's existing copy and translations."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import subprocess
import urllib.request
import urllib.parse

ROOT = Path(__file__).resolve().parents[2]


def normalize(value):
    return re.sub(r"\s+", " ", value).strip()


class Element:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def descendants(self):
        for child in self.children:
            if isinstance(child, Element):
                yield child
                yield from child.descendants()


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = self.current = Element("document")
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        element = Element(tag, attrs, self.current)
        self.current.children.append(element)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.current = element

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        element = self.current
        while element.parent:
            if element.tag == tag:
                self.current = element.parent
                return
            element = element.parent

    def handle_data(self, data):
        self.current.children.append(data)


def matches(element, selector):
    has = re.search(r":has\(([^)]+)\)", selector)
    if has and not any(matches(child, has[1]) for child in element.descendants()):
        return False
    negation = re.search(r":not\(\[([^]]+)\]\)", selector)
    if negation and negation[1] in element.attrs:
        return False
    nth = re.search(r":nth-child\((\d+)\)", selector)
    if nth:
        if element.parent is None:
            return False
        siblings = [child for child in element.parent.children if isinstance(child, Element)]
        if siblings.index(element) + 1 != int(nth[1]):
            return False
    selector = re.sub(r":(?:has|not|nth-child)\([^)]*\)", "", selector)
    tag = re.match(r"^[a-z][\w-]*", selector)
    if tag and element.tag != tag[0]:
        return False
    if any(value not in element.attrs.get("class", "").split() for value in re.findall(r"\.([\w-]+)", selector)):
        return False
    ident = re.search(r"#([\w-]+)", selector)
    return not ident or element.attrs.get("id") == ident[1]


def chain(element, tokens):
    if not element or not matches(element, tokens[-1]):
        return False
    if len(tokens) == 1:
        return True
    if tokens[-2] == ">":
        return chain(element.parent, tokens[:-2])
    if tokens[-2] == "+":
        siblings = [child for child in element.parent.children if isinstance(child, Element)]
        position = siblings.index(element)
        return position > 0 and chain(siblings[position - 1], tokens[:-2])
    parent = element.parent
    while parent:
        if chain(parent, tokens[:-1]):
            return True
        parent = parent.parent
    return False


export = subprocess.check_output(["node", "--input-type=module", "-e", """
import fs from 'node:fs';
const load=async path=>import('data:text/javascript;base64,'+fs.readFileSync(path).toString('base64'));
const {dictionary}=await load('frontend/js/i18n/dictionary.js');
const {contentSlots}=await load('frontend/js/models/SiteContentModel.js');
console.log(JSON.stringify({dictionary,contentSlots}));
"""], cwd=ROOT)
manifest = json.loads(export)
dictionary = {normalize(row[0]): row for row in manifest["dictionary"]}
documents = {page: Document((ROOT / "frontend" / ("index.html" if page == "home" else page + ".html")).read_text(encoding="utf-8")) for page in {slot["page"] for slot in manifest["contentSlots"]}}


def content(element, language):
    if isinstance(element, str):
        row = dictionary.get(normalize(element))
        return row[language] if row else element
    if element.tag == "br":
        return " "
    raw = normalize("".join(content(child, 0) for child in element.children))
    if raw in dictionary:
        return dictionary[raw][language]
    return normalize(" ".join(content(child, language) for child in element.children))


env = dict(line.split("=", 1) for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if "=" in line and not line.startswith("#"))
login = urllib.request.Request("http://localhost/api/auth/login", data=urllib.parse.urlencode({"username": env["ADMIN_USERNAME"], "password": env["ADMIN_PASSWORD"]}).encode())
with urllib.request.urlopen(login) as response:
    token = json.load(response)["access_token"]

# Resolve the entire manifest before making changes, so a missing selector fails early.
payloads = []
for slot in manifest["contentSlots"]:
    fields = {}
    for field in ("title", "content"):
        if field in slot:
            tokens = re.findall(r"[^ >+]+|[>+]", slot[field])
            element = next((item for item in documents[slot["page"]].root.descendants() if chain(item, tokens)), None)
            if element is None:
                raise ValueError(f"Missing selector: {slot['code']} / {slot[field]}")
            fields[field] = element
    payloads.append((slot["code"], {"page_code": slot["page"], "is_active": True, "translations": [
        {"locale": locale, **{field: content(element, index) for field, element in fields.items()}}
        for index, locale in enumerate(("rus", "eng", "ger"))
    ]}))

for code, payload in payloads:
    request = urllib.request.Request("http://localhost/api/content_blocks/" + code,
        data=json.dumps(payload).encode(), method="PUT",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urllib.request.urlopen(request) as response:
        json.load(response)
print(f"Filled {len(payloads)} admin text slots in three languages.")
