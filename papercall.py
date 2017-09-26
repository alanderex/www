import sys
import json
import mistune
from jinja2 import Template
import re
from unicodedata import normalize
import os
from openpyxl import load_workbook


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
_regex = re.compile('[^a-z0-9]')
#First parameter is the replacement, second parameter is your input string


def slugify(text, delim=u'-'):
    """Generates an slightly worse ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        word = word.decode('ascii')
        word = _regex.sub('', word)
        if word:
            result.append(word)
    return str(delim.join(result))

def enrich(entry):
    entry["slug"] = slugify(entry["title"])
    entry["tags_str"] = " ".join(entry["tags"][:10]) 
    return entry

#data = json.load(open("submissions.json"))
data = json.load(open("speakers_accepted.json"))
data = list(filter(lambda entry: entry["state"] == "accepted", data))
data = list(map(enrich, data))
data.sort(key=lambda entry: entry["title"])

# for d in data:
#     if d['slug'] == 'an-introduction-to-pymc3':
#         d['name'] = 'Adrian Seyboldt'
#     elif d['slug'] == 'getting-scikit-learn-to-run-on-top-of-pandas':
#         d['name'] = 'Ami Tavory'
#     elif d['slug'] == 'metaclasses-when-to-use-and-when-not-to-use':
#         d['description'] = d['description'].replace("# Description", "")
#     elif d['name'] == "Jens Nie":
#         d['name'] = "Jens Nie,Andre Lengwenus"
#     elif d['name'] == "Ines Dorian Gütt":
#         d['name'] = "Ines Dorian Gütt,Marie Dedikova"
#     elif d['name'] == "Thomas Reifenberger":
#         d['name'] = "Thomas Reifenberger,Martin Foertsch"


def get_talk(speaker):
    for d in data:
        if d["name"] == speaker:
            return d



tpl = """_model: page_markdown
---
title: {{title}}
---
head_extra:

<meta name="twitter:card" content="summary" />
<meta name="twitter:site" content="@pyconde" />
<meta name="twitter:title" content="{{name|escape}}: {{title|escape}}" />
<meta name="twitter:description" content="{{abstract|escape}}" />
<meta name="twitter:image" content="https://de.pycon.org/files/logo.png" />
---
body:

# {{title}}
<div class="avatar">
![]({{avatar}})
**[{{name}}]({{url}})** {% if twitter %}([@{{twitter}}](http://twitter.com/{{twitter}})){% endif %}


{{bio}}
</div>
## Abstract
{%if tags_str %}
*Tags:* {{tags_str}}{%endif%}

{{abstract}}


## Description
{{description}}

"""


tpl_index = """_model: page_markdown
---
title: {{kind|capitalize}}
---
body:

{% for entry in data %}
# [{{entry.title}}](./{{entry.slug}}/)
**{{entry.name}}**

{{entry.abstract}}

{% endfor %}
"""

template = Template(tpl)
template_index = Template(tpl_index)

tutorials = ['practical-data-cleaning-101', 
             'machine-learning-as-a-service',
            'metaclasses-when-to-use-and-when-not-to-use',
            'network-analysis-using-python',
            'topic-modelling-and-a-lot-more-with-nlp-framework-gensim',
            'python-on-bare-metal-beginners-tutorial-with-micropython-on-the-pyboard',
            'how-to-fund-your-company'
            ]


def dump(entry, kind='tutorials'):
    dirname = 'pyconde/content/schedule/{}/{}/'.format(kind, entry['slug'])
    print(dirname)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)
    with open(os.path.join(dirname, 'contents.lr'), 'w') as f:
        f.write(template.render(entry))


def gen():
    d = filter(lambda entry: entry["slug"] in tutorials, data)
    with open('pyconde/content/schedule/tutorials/contents.lr', 'w') as f:
        f.write(template_index.render(kind="tutorials", data=d))
    
    d = filter(lambda entry: entry["slug"] not in tutorials, data)
    with open('pyconde/content/schedule/talks/contents.lr', 'w') as f:
        f.write(template_index.render(kind="talks", data=d))

    for entry in filter(lambda entry: entry["slug"] in tutorials, data):
        dump(entry)
        #print(template.render(entry))
    for entry in filter(lambda entry: entry["slug"] not in tutorials, data):
        dump(entry, kind='talks')

def bada():
    tpl = """#PyConDE Talk @{twitter}:
{title}

https://de.pycon.org/schedule/talks/{slug}/"""
    for entry in data:
        print(tpl.format(**entry))
        print("\n---\n\n")


def parse(s):
    if "available" in s:
        return {}
    first, speaker = s.split("[[")
    speaker = speaker.rstrip("]")
    tags = first.rsplit('(',1)[1].rstrip(")")
    tags = [x.strip() for x in tags.split("|") if x.strip() and x.strip() != "Other"]
    if speaker == "adrian.seyboldt@gmail.com":
        speaker = 'Adrian Seyboldt'
    elif speaker == "atavory@gmail.com":
        speaker = 'Ami Tavory'

    talk = get_talk(speaker)

    
    if talk is None:
        print(speaker)
        talk = {"title": "FIXE", "slug": "FIXME"}
    return {"speaker": speaker, "tags": tags, "title": talk["title"], "slug": talk["slug"]}

def gen_schedule_databag():
    wb = load_workbook('schedule.xlsx')
    sheet = wb['Sheet1']

    d1 = [2,3,5,6,8,9]
    d2 = [11,12,13,15,16,18,19]
    d3 = [21,22,23,25,26]
    talks = {}
    for day, rows in enumerate([d1,d2,d3]):
        for row_nr, row in enumerate(rows):
            key = "THEATRE_{}_{}".format(day+1,row_nr+1)
            value = sheet["C{}".format(row)].value
            talks[key] = parse(value)
            
            key = "LECTURE_{}_{}".format(day+1,row_nr+1)
            value = sheet["E{}".format(row)].value
            talks[key] = parse(value)


            key = "FLOOR_{}_{}".format(day+1,row_nr+1)
            value = sheet["B{}".format(row)].value
            talks[key] = parse(value)

    json.dump(talks, open("pyconde/databags/talks.json", "w"), indent=4)

    tutorials = {}
    for day, rows in enumerate([[2,5,8],[11,15,18],[21,25]]):
        for row_nr, row in enumerate(rows):
            key = "MUSEUM_{}_{}".format(day+1,row_nr+1)
            value = sheet["D{}".format(row)].value
            tutorials[key] = parse(value)
    json.dump(tutorials, open("pyconde/databags/tutorials.json", "w"), indent=4)


def main(args=None):
    if args is None:
        args = sys.argv
    gen() 
    #bada() 
    gen_schedule_databag() 

if __name__ == "__main__":
    main()
