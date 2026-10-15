"""Flask-приложение: система уведомлений на паттерне Bridge."""
from flask import Flask, render_template, request, redirect, url_for, flash, abort

from db import get_db, init_db
from patterns.bridge import CHANNELS, PRIORITIES, create_notification

app = Flask(__name__)
app.secret_key = "change-me-in-production"

MESSAGE_MIN, MESSAGE_MAX = 3, 500


# ---------------------------------------------------------------- helpers
def validate(form):
    """Проверяет данные формы. Возвращает (очищенные данные, список ошибок)."""
    message = (form.get("message") or "").strip()
    ntype = form.get("notification_type", "")
    priority = form.get("priority", "")
    errors = []

    if not message:
        errors.append("Введите текст сообщения.")
    elif len(message) < MESSAGE_MIN:
        errors.append(f"Сообщение слишком короткое: минимум {MESSAGE_MIN} символа.")
    elif len(message) > MESSAGE_MAX:
        errors.append(f"Сообщение слишком длинное: максимум {MESSAGE_MAX} символов.")
    if ntype not in CHANNELS:
        errors.append("Выберите тип уведомления из списка.")
    if priority not in PRIORITIES:
        errors.append("Выберите приоритет из списка.")

    return {"message": message, "notification_type": ntype, "priority": priority}, errors


def get_or_404(notification_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,)).fetchone()
    conn.close()
    if row is None:
        abort(404)
    return row


def form_context(**extra):
    return dict(channels=list(CHANNELS), priorities=list(PRIORITIES), limit=MESSAGE_MAX, **extra)


# ------------------------------------------------------------------- READ
@app.route("/")
def index():
    ntype = request.args.get("type", "")
    priority = request.args.get("priority", "")

    query, params = "SELECT * FROM notifications WHERE 1=1", []
    if ntype in CHANNELS:
        query += " AND notification_type = ?"
        params.append(ntype)
    if priority in PRIORITIES:
        query += " AND priority = ?"
        params.append(priority)
    query += " ORDER BY id DESC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return render_template(
        "index.html", rows=rows, selected_type=ntype, selected_priority=priority,
        channels=list(CHANNELS), priorities=list(PRIORITIES),
    )


@app.route("/notification/<int:notification_id>")
def detail(notification_id):
    row = get_or_404(notification_id)
    # Здесь работает мост: приоритет + канал собираются из данных записи.
    delivery = create_notification(row["notification_type"], row["priority"]).send(row["message"])
    return render_template("detail.html", row=row, delivery=delivery)


# ----------------------------------------------------------------- CREATE
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        data, errors = validate(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("add.html", **form_context(data=data)), 400
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO notifications (message, notification_type, priority) VALUES (?, ?, ?)",
            (data["message"], data["notification_type"], data["priority"]),
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        flash("Уведомление добавлено.", "success")
        return redirect(url_for("detail", notification_id=new_id))
    return render_template("add.html", **form_context(data={"priority": "Normal"}))


# ----------------------------------------------------------------- UPDATE
@app.route("/edit/<int:notification_id>", methods=["GET", "POST"])
def edit(notification_id):
    row = get_or_404(notification_id)
    if request.method == "POST":
        data, errors = validate(request.form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("edit.html", **form_context(data=data, row=row)), 400
        conn = get_db()
        conn.execute(
            "UPDATE notifications SET message = ?, notification_type = ?, priority = ? WHERE id = ?",
            (data["message"], data["notification_type"], data["priority"], notification_id),
        )
        conn.commit()
        conn.close()
        flash("Изменения сохранены.", "success")
        return redirect(url_for("detail", notification_id=notification_id))
    return render_template("edit.html", **form_context(data=dict(row), row=row))


# ----------------------------------------------------------------- DELETE
@app.route("/delete/<int:notification_id>", methods=["POST"])
def delete(notification_id):
    get_or_404(notification_id)
    conn = get_db()
    conn.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()
    flash("Уведомление удалено.", "success")
    return redirect(url_for("index"))


# ------------------------------------------------------ Bridge demonstration
@app.route("/pattern", methods=["GET", "POST"])
def pattern():
    """Показывает матрицу 3x3: один текст проходит через все пары приоритет + канал."""
    sample = "Занятие по Flask начнётся в 10:00 в аудитории 305."
    if request.method == "POST":
        sample = (request.form.get("sample") or "").strip()[:MESSAGE_MAX] or sample
    matrix = [
        [create_notification(c, p).send(sample) for c in CHANNELS]
        for p in PRIORITIES
    ]
    return render_template(
        "pattern.html", sample=sample, matrix=matrix,
        channels=list(CHANNELS), priorities=list(PRIORITIES),
    )


# ---------------------------------------------------------- error handlers
@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, text="Такой записи нет. Возможно, её уже удалили."), 404


@app.errorhandler(405)
def not_allowed(_):
    return render_template("error.html", code=405, text="Это действие недоступно по такому адресу."), 405


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
