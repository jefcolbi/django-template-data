# Django Template Data

### Why?

You are working on a Django project and you want a way to update some strings 
or blocks without using a bare CMS or a WYSIWYG. Then this small module is for
 you. It does what you expect, load datas from database and send them via
 the context to the templates.

### Installation

    $ pip install git+https://github.com/jefcolbi/django-template-data.git

### Usage

Add 'template_data' in INSTALLED_APPS  

```python
INSTALLED_APPS = [
    ...,
    'template_data',
    ...,
]
```

Then add `load_data()` to templates context processors

```
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                ...,
                'template_data.processors.load_data',
            ],
        },
    },
]
```

Finally migrate

    $ python manage.py migrate

### Tutorial

Let say you want a dynamic title, loaded from the database. First create a base
 template like this:

```html
{% load i18n %}
<!doctype html>
<html lang="en">

<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="shortcut icon" href="/static/front/img/favicon.png" type="image/x-icon">
    {% block full_title %}<title>{% block title %}{{ title }}{% endblock %} - Sitename</title>{% endblock %}

...
```

Go to your Django admin to manage TemplateData model. Create two rows, with these
values:  
key = "title", page = "index", value = "Home"  
key = "title", page = "signin", value = "Login in your account"  
As you can imagine the title of the index page will be "Home - Sitename" and
 for the signin page will be "Login in your account - Sitename"

You surely noticed how we appended "- Sitename" to the title in the template.
 We can do the same by using the inheriting feature.  
First we define this template:

```html
{% load i18n %}
<!doctype html>
<html lang="en">

<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="shortcut icon" href="/static/front/img/favicon.png" type="image/x-icon">
    <title>{% block title %}{{ title }}{% endblock %}</title>

...
```

Then create three rows of TemplateData with these values:  
key = "title", page = "global", value = "Sitename"  
key = "title", page = "index", inheriting_page = "global", value = "Home - {{ super }}"  
key = "title", page = "signin", inheriting_page = "global", value = "Login in your account - {{ super }}"  
You will have the same result.

#### 			Internalization

You can also add the lang attribute for multilingualism, but for this to work you need to set the LANGUAGE variables in your project settings.

```html
{% load i18n %}
<!doctype html>
<html lang="en">

<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <link rel="shortcut icon" href="/static/front/img/favicon.png" type="image/x-icon">
    {% block full_title %}<title>{% block title %}{{ title }}{% endblock %} - Sitename</title>{% endblock %}

...
```



Go to your Django admin to manage TemplateData model. Create two rows, with these
values:  
key = "title", page = "signin", lang = english, value = "Login in your account"  

key = "title", page = "signin", lang = french, value = "Connexion a votre compte"  

As you can imagine the title of the signin page will be "Login in your account - Sitename" if browser language is in english and
  "Connexion a votre compte - Sitename" if french



#### 	Restore data

After saving in bd all the texts, use the command`python  manage.py save_data file_name.json` to save all that in a json file. 

To restore these data in your database use  `python manage.py restore_data file_name.json`


### Template rewriting

#### Edit

Template rewriting is a feature provided to re-write existing templates to conform with Django Template Data.

Start by editing your templates and add the attribute `tpl-data-key` in the tags you want to create template data for.  
For example, if you have a h2 tag like this  
`<h2>My custom title</h2>`

you can edit it like this  
`<h2 tpl-data-key="title">My custom title</h2>`

It will be rewritten in  
`<h2>{{ title }}</h2>`  

and a new template data entry will be added in database.

You can inform about the tag's text language by using `tpl-data-lang` like  
`<h2 tpl-data-key="title" tpl-data-lang="en">My custom title</h2>`  
to inform that your text is in English.

#### Process

After you have edited your templates files run the django command `rewrite_template`  
Examples:

To rewrite all the templates linked to your views, do:  
`python manage.py rewrite_template --views`

To rewrite a single base template file, do:  
`python manage.py rewrite_template --file=core/base.html`

To rewrite a single template file, do:  
`python manage.py rewrite_template --file=core/index.html --pagename=index`

### Contributing

Contributions are welcome. It is FOSS!

### License

Feel free to use it as you want.
