import sys
import json
import mistune
from jinja2 import Template
import re
from unicodedata import normalize
import os


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

data = json.load(open("submissions.json"))
data = list(filter(lambda entry: entry["state"] == "accepted", data))
data = list(map(enrich, data))
data.sort(key=lambda entry: entry["title"])


tpl = """_model: page_markdown
---
title: {{title}}
---
body:

# {{title}}
<div class="avatar">
![]({{avatar}})
**[{{name}}]({{url}})**


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
            'how-to-found-a-company',
            'python-on-bare-metal-beginners-tutorial-with-micropython-on-the-pyboard'
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
    for entry in data:
        print(entry["slug"])
        print(entry["name"])
        print(entry["avatar"])
        print()

def main(args=None):
    if args is None:
        args = sys.argv
    gen() 
    #bada() 

if __name__ == "__main__":
    main()
