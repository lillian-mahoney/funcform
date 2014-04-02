formhandler
===========

Sometimes the web interface is an afterthought.

I've learned what I /really/ want from a web framework: as little work or involvement on my part as possible. So that's what formhandler does.

In ONE command you can have a CGI script which will act as the HTML input form (for sending data to function), and then it will also handle post/get data--utilized for evaluating form input, and providing HTML output from the evaluation. All (mostly) auto-magically.

# Get started:

1. Launch testhttpd.py
2. Open http://127.0.0.1:8080/test.py in a web browser.
3. Open test.py in a file editor to see what's going on!

# Example Usage

Say we want a web interace for these functions (see: test.py):

```python
def make_uppercase(s):
    """This description shows up in the form."""
    return s.upper()

def reflect(upload_file, save_directory=None):
    """Simply display an uploaded image."""

    if save_directory and save_directory in ('resources', 'uploads'):
        path = os.path.join(save_directory, upload_file.filename)
    else:
        path = upload_file.filename

    with file(path, 'wb') as f:
        f.write(upload_file.file.read())

    return '<img src="/%s" alt="user uploaded file" />' % path
```

All we have to to is:

```python
types = {'upload_file': 'file', 'save_directory': ['uploads', 'resources'],}
print 'Content-Type: text/html\n'
print form_handler(make_uppercase, reflect, reflect=types)
```
