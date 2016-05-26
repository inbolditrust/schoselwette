#!venv/bin/python3

from wette import app

if __name__ == '__main__':
    print(app.config['APPLICATION_ROOT'])
    app.run(debug=True)
