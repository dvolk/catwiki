import datetime as dt
import difflib
import time

import argh
import flask
import flask_mongoengine as fm
import humanize

import to_md

app = flask.Flask(__name__)
app.secret_key = "secret"
app.config["MONGODB_DB"] = "catwiki-1"
db = fm.MongoEngine(app)


class Page(db.Document):
    title = db.StringField(max_length=128)
    content = db.StringField()
    created_epochtime = db.IntField(default=0)
    modified_epochtime = db.IntField(default=0)


class Change(db.Document):
    page_id = db.ReferenceField(Page)
    diff_str = db.StringField()
    diff_epochtime = db.IntField()


def icon(name):
    return f'<i class="fa fa-{name} fa-fw"></i>'


PageForm = fm.wtf.model_form(Page)


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
            old_content = p.content
            new_content = form.content.data.replace("\r", "")
            if old_content == new_content:
                return flask.redirect(flask.url_for("view", page_title=page_title))
            p.title = form.title.data
            p.content = new_content
            p.modified_epochtime = int(time.time())
        else:
            old_content = str()
            new_content = form.content.data.replace("\r", "\n")
            p = Page(title=form.title.data, content=new_content)
            p.modified_epochtime = int(time.time())
            p.created_epochtime = int(time.time())

        new_diff = [x.strip() for x in new_content.split("\n")]
        old_diff = [x.strip() for x in old_content.split("\n")]
        print(new_diff, old_diff)
        p.save()
        change = Change(
            page_id=p.id,
            diff_str="\n".join(difflib.unified_diff(old_diff, new_diff, lineterm="")),
            diff_epochtime=int(time.time()),
        )
        change.save()
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


@app.route("/page_changes/<page_title>/<page>")
def page_changes(page_title, page):
    time_now = int(time.time())

    def nice_time(t2):
        return humanize.naturaltime(dt.timedelta(seconds=(time_now - t2))).capitalize()

    page_id = Page.objects(title=page_title).first_or_404().id
    changes = (
        Change.objects(page_id=page_id)
        .order_by("-diff_epochtime")
        .paginate(page=int(page), per_page=10)
    )
    return flask.render_template(
        "page_changes.jinja2",
        changes=changes,
        nice_time=nice_time,
        page=int(page),
        page_title=page_title,
    )


def main():
    app.run(host="0", port=7755, debug=True)


if __name__ == "__main__":
    argh.dispatch_command(main)
