import datetime as dt
import logging
import subprocess
import time
from pathlib import Path

import argh
import flask
import git
import humanize
from flask_mongoengine import *

import to_md

app = flask.Flask(__name__)
app.secret_key = "secret"
app.config["MONGODB_DB"] = "catwiki-1"
db = MongoEngine(app)


class Page(db.Document):
    title = db.StringField(max_length=128)
    content = db.StringField()
    created_epochtime = db.IntField(default=0)
    modified_epochtime = db.IntField(default=0)


def icon(name):
    return f'<i class="fa fa-{name} fa-fw"></i>'


PageForm = wtf.model_form(Page)


@app.context_processor
def inject_globals():
    return {
        "icon": icon,
        "to_md": to_md.text_to_html,
    }


@app.route("/")
def index():
    return flask.redirect(flask.url_for("view", page_title="index"))


@app.route("/view/<page_title>")
def view(page_title):
    p = Page.objects(title=page_title).first()
    if not p:
        return flask.redirect(flask.url_for("edit", page_title=page_title))
    else:
        return flask.render_template(
            "view.jinja2", page_title=page_title, p=p, title="CatWiki " + page_title
        )


@app.route("/edit/<page_title>", methods=["GET", "POST"])
def edit(page_title):
    form = PageForm(flask.request.form)
    p = Page.objects(title=page_title).first()
    if flask.request.method == "POST" and form.validate():
        if p:
            p.title = form.title.data
            p.content = form.content.data
            p.modified_epochtime = int(time.time())
        else:
            p = Page(title=form.title.data, content=form.content.data)
            p.modified_epochtime = int(time.time())
            p.created_epochtime = int(time.time())
        p.save()
        return flask.redirect(flask.url_for("view", page_title=page_title))
    else:
        return flask.render_template(
            "edit.jinja2",
            page_title=page_title,
            p=p,
            form=form,
            title="CatWiki Edit " + page_title,
        )


@app.route("/recent_changes")
def recent_changes():
    time_now = int(time.time())

    def nice_time(t2):
        return humanize.naturaltime(dt.timedelta(seconds=(time_now - t2))).capitalize()

    pages = Page.objects().order_by("-modified_epochtime")
    return flask.render_template(
        "recent_changes.jinja2", pages=pages, nice_time=nice_time
    )


def main():
    app.run(port=7755, debug=True)


if __name__ == "__main__":
    argh.dispatch_command(main)
