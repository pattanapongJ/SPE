from odoo import http


def guess_db(httprequest):
    """Let's try to find database for the API request."""
    # Headers
    db_keys = ['instance', 'db', 'database']
    for key in db_keys:
        if httprequest.headers.get(key):
            return httprequest.headers.get(key)
        elif httprequest.args.get(key):
            return httprequest.args.get(key)


before = http.Root.setup_db
def after(cls, httprequest):
    assumed_db = guess_db(httprequest)
    if assumed_db:
        print(assumed_db, type(assumed_db))
        httprequest.session.db = assumed_db
    before(cls, httprequest)
http.Root.setup_db = after
