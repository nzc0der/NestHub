from backend.app import app

if __name__ == '__main__':
    # init_db is handled within backend/app.py's __main__ block,
    # but since we are importing 'app', we might need to ensure
    # the database is initialized if we run this instead of app.py.
    # Looking at backend/app.py:
    # if __name__ == '__main__':
    #     with app.app_context():
    #         init_db(app)
    #     app.run(debug=True, port=8000, host='0.0.0.0')

    from backend.database.db import init_db
    with app.app_context():
        init_db(app)
    app.run(debug=True, port=8000, host='0.0.0.0')
