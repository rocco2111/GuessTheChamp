import json
import feedparser
import os
import random
from flask import Flask, render_template, request, session, jsonify, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

with open("champions.json", "r", encoding="utf-8") as f:
    CHAMPS = json.load(f)


def build_question(exclude=None):
    """
    Returns a question dict:
      { image: str, correct: str, options: [str, str, str] }
    If exclude filters out all champs, returns None.
    """
    exclude = exclude or set()

    pool = [c for c in CHAMPS if c["name"] not in exclude]
    if not pool:
        return None  # <- FIX: verhindert random.choice([]) Crash

    correct = random.choice(pool)

    wrong_pool = [c for c in CHAMPS if c["name"] != correct["name"]]
    # Sicherheitscheck (falls champions.json zu klein ist)
    if len(wrong_pool) < 2:
        return None

    wrong = random.sample(wrong_pool, 2)

    options = [correct["name"], wrong[0]["name"], wrong[1]["name"]]
    random.shuffle(options)

    return {
        "image": correct["image"],
        "correct": correct["name"],
        "options": options
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/quiz/<mode>")
def quiz(mode):
    if mode not in ("freestyle", "competition"):
        return redirect(url_for("index"))

    session.clear()
    session["mode"] = mode

    if mode == "competition":
        count = int(request.args.get("count", "10"))
        if count not in (10, 20, 50):
            count = 10

        # optional: falls du weniger Champs als count hast, begrenzen
        session["total"] = min(count, len(CHAMPS))

        session["i"] = 0
        session["score"] = 0
        session["asked"] = []

    return render_template("quiz.html", mode=mode)


@app.route("/api/next")
def api_next():
    mode = session.get("mode", "freestyle")

    if mode == "competition":
        i = session.get("i", 0)
        total = session.get("total", 10)

        if i >= total:
            return jsonify({"done": True})

        asked = set(session.get("asked", []))
        q = build_question(exclude=asked)

        # FIX: wenn keine neuen Champs mehr möglich -> done
        if q is None:
            return jsonify({"done": True})

        asked.add(q["correct"])
        session["asked"] = list(asked)

        return jsonify({
            "done": False,
            "mode": "competition",
            "i": i + 1,
            "total": total,
            "question": {"image": q["image"], "options": q["options"]},
            "correct": q["correct"]
        })

    # Freestyle: endlos (darf wiederholen)
    q = build_question()
    # falls champions.json zu klein/kaputt ist
    if q is None:
        return jsonify({"done": True})

    return jsonify({
        "done": False,
        "mode": "freestyle",
        "question": {"image": q["image"], "options": q["options"]},
        "correct": q["correct"]
    })


@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.get_json(force=True)
    picked = data.get("picked", "")
    correct = data.get("correct", "")

    right = (picked == correct)

    if session.get("mode") == "competition":
        if right:
            session["score"] = session.get("score", 0) + 1
        session["i"] = session.get("i", 0) + 1

    return jsonify({"ok": True, "right": right})


@app.route("/api/finish", methods=["POST"])
def api_finish():
    # beendet Competition vorzeitig (zeigt Ergebnis im Popup)
    if session.get("mode") == "competition":
        session["i"] = session.get("total", session.get("i", 0))
    return jsonify({"ok": True})


@app.route("/api/result")
def api_result():
    return jsonify({
        "score": session.get("score", 0),
        "total": session.get("total", 0)
    })


@app.route("/result")
def result():
    return render_template(
        "result.html",
        score=session.get("score", 0),
        total=session.get("total", 0)
    )


@app.route("/impressum")
def impressum():
    return render_template("impressum.html")


if __name__ == "__main__":
    app.run(debug=True)

@app.route("/api/news")
def api_news():
    feeds = [
        "https://www.leagueoflegends.com/en-us/news/feed.xml",
        "https://www.leagueoflegends.com/en-us/news/tags/patch-notes/feed.xml",
        "https://www.leagueoflegends.com/en-us/news/tags/dev/feed.xml",
    ]

    items = []
    for url in feeds:
        feed = feedparser.parse(
            url,
            request_headers={"User-Agent": "GuessTheChamp-CS50/1.0"}
        )

        for entry in feed.entries:
            items.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "date": entry.get("published", "").strip()[:16]
            })

        # Wenn wir schon genug haben, abbrechen
        if len(items) >= 8:
            break

    # Duplikate nach Link entfernen
    seen = set()
    unique = []
    for it in items:
        if it["link"] and it["link"] not in seen:
            seen.add(it["link"])
            unique.append(it)
        if len(unique) == 8:
            break

    return jsonify(unique)
