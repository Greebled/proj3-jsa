"""
Flask web site with vocabulary matching game
(identify vocabulary words that can be made 
from a scrambled string)
"""

import flask
import logging

# Our own modules
from letterbag import LetterBag
from vocab import Vocab
from jumble import jumbled
import config

###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Should allow using session variables

#
# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.  Otherwise we would have to
# store it in the browser and transmit it on each request/response cycle,
# or else read it from the file on each request/responce cycle,
# neither of which would be suitable for responding keystroke by keystroke.

WORDS = Vocab(CONFIG.VOCAB)

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    """The main page of the application"""
    flask.g.vocab = WORDS.as_list()
    flask.session["target_count"] = min(
        len(flask.g.vocab), CONFIG.SUCCESS_AT_COUNT)
    flask.session["jumble"] = jumbled(
        flask.g.vocab, flask.session["target_count"])
    flask.session["matches"] = []
    app.logger.debug("Session variables have been set")
    return flask.render_template('vocab.html')



@app.route("/success")
def success():
    return flask.render_template('success.html')

#######################
# Form handler.
# CIS 322 note:
#   You'll need to change this to a
#   a JSON request handler
#######################


@app.route("/_check")
def check():
    """
    User has submitted the form with a word ('attempt')
    that should be formed from the jumble and on the
    vocabulary list.  We respond depending on whether
    the word is on the vocab list (therefore correctly spelled),
    made only from the jumble letters, and not a word they
    already found.
    """
    text = flask.request.args.get("text", "", type=str).strip().lower()
    jumble = flask.session.get("jumble", "")
    matches = flask.session.get("matches", [])  # Default to empty list
    target_count = flask.session.get("target_count", 1)

    # Is it good?
    in_jumble = LetterBag(jumble).contains(text)
    matched = WORDS.has(text)

    new_match = False
    message = ""
    if len(text) == 0:
        pass
    elif matched and in_jumble and text not in matches:
        # Cool, they found a new word
        matches.append(text)
        flask.session["matches"] = matches
        new_match = True
    elif text in matches:
        message = "You already found {}".format(text)
    elif not in_jumble:
        message = '"{}" can\'t be made from the letters {}'.format(
            text, jumble)

    rslt = {
        "word": text,
        "new_match": new_match,
        "message": message,
        "success": len(matches) >= target_count
    }
    return flask.jsonify(result=rslt)


###################
#   Error handlers
###################


@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404


@app.errorhandler(500)
def error_500(e):
    app.logger.warning("++ 500 error: {}".format(e))
    assert not True  # I want to invoke the debugger
    return flask.render_template('500.html'), 500


@app.errorhandler(403)
def error_403(e):
    app.logger.warning("++ 403 error: {}".format(e))
    return flask.render_template('403.html'), 403


####

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
    app.logger.info(
        "Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=CONFIG.PORT, host="0.0.0.0")
