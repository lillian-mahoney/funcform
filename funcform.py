#!/usr/local/bin/python
"""funcform: sometimes the web interface is an afterthought.
Lillian Lynn Mahoney

PURPOSE:
  Pipe input from web form to a Python function, pipe output back to a
  web page. Make this process require as little code as possible.

  Includes tools for automatically converting data returned from a
  function, to HTML, e.g., dict > html, list > html, etc.

RECOMMENDATIONS:
  Do not even consider formhandler in your development process. Then,
  make a single function which acts as the interface/form handler, to
  be utilized with formhandler.

DEVELOPER NOTES:
  - Makes heavy usage of the "cgi" module.

USAGE/EXAPMLES:
  >>>

BONUS:
  Includes tool for editing parts of the template, an example
  tool which edits an SQLITE database/table.

"""

import os
import cgi
import cgitb; cgitb.enable()
import inspect
from cStringIO import StringIO
import textwrap


# CONFIG/CONSTANTS ############################################################


FORM = '''
       <form enctype="multipart/form-data" method="post">
         <fieldset>
           <legend>{title}</legend>
           {about}
           {hidden trigger field}
           {fields}
           <input type="submit" value="Process: {title}">
         </fieldset>
       </form>
       '''
SELECT = '''
         <label for="{argument name}">{argument title}</label>
         <select name="{argument name}" id="{argument name}">
           {options}
         </select>
         '''
HTML_INPUT_FIELD = '''
                   <label for="{argument name}">
                     {argument title}
                   </label>
                   <input type="{input type}" 
                          name="{argument name}"
                          id="{argument name}">
                   <br>
                   '''


# GENERIC PYTHON DATA > HTML ##################################################


# a common way I build HTML
template = lambda s, d: textwrap.dedent(s.format(**d))

# Python variable name to user-friendly name.
var_title = lambda s: s.replace('_', ' ').title()


# Simply convert a string into HTML paragraphs.
paragraphs = lambda s: '\n\n'.join(['<p>%s</p>' % p for p in s.split('\n\n')])


def docstring_html(function):
    """Makes some nice HTML out of a function's DocString, attempting
    Google's style guide (see: my code!).

    A work in progress. I will try to use someone else's library
    for this!

    """

    # this should use template()
        # this should use template()
    html = StringIO()
    html.write('<section class="form-help">\n')
    html.write('<pre>\n')
    html.write(inspect.getdoc(function))
    html.write('</pre>\n')
    html.write('</section>\n')

    return html.getvalue()


def iter_dicts_table(iter_dicts):
    """Convert an iterable sequence of dictionaries (all of which with
    identical keys) to an HTML table.

    Args:
      iter_dicts: an iterable sequence (list, tuple) of dictionaries,
        dictionaries having identical keys.

    Returns:
      str|None: HTML tabular representation of a Python iterable sequence of
        dictionaries which share identical keys. Returns None if table
        is not consistent (dictionary keys).

    """

    # first check key consistency
    first_keys = iter_dicts[0].keys()

    for d in evaluation:

        if d.keys() != first_keys:

            return None

    html = StringIO()
    keys = ['<td>%(' + key + ')s</td>' for key in iter_dicts[0]]
    row = '<tr>' + ''.join(keys) + '</tr>'
    html.write('<table>')

    for d in iter_dicts:
        html.write(row % d)

    html.write('</table>')

    return html.getvalue()


# The juice ###################################################################


class FuncForm(object):

    def __init__(self, function, argument_types=None):
        self.function = function
        self.name = function.__name__
        self.argument_types = argument_types or {}

        args, __, kwargs, __ = inspect.getargspec(function)
        self.args = args or []
        self.kwargs = kwargs or {}

    def to_form(self):
        """Returns the HTML input form for a function.

        Returns:
          str: HTML input form, for submitting arguments to a python
            function, via POST/GET.

        """

        # Form configuration/pre-setup.
        title = var_title(self.name)

        # Create HTML input labels and respective fields,
        # based on (keyword) argument names and arg_map (above).
        # Create said fields for required_fields and optional_fields.
        fields = []

        for argument in self.args + self.kwargs.keys():
            # argument_type may be 'text', 'file', or a Python list,
            # representing options in a select field.
            argument_type = self.argument_types.get(argument, 'text')
            parts = {
                     'argument name': argument,
                     'argument title': var_title(argument),
                    }

            if isinstance(argument_type, list):
                # build <select> <options> from the list
                # denoted as the argument type
                options = argument_type
                option = '<option value="%s">%s</option>'
                options = [option % (o, var_title(o)) for o in options]
                parts['options'] = '\n'.join(options)
                new_field = SELECT

            elif argument_type in ('text', 'file'):
                parts['input type'] = argument_type
                new_field = HTML_INPUT_FIELD

            else:

                raise Exception('invalid argument type')

            fields.append(template(new_field, parts))

        # build form_parts...
        form_parts = {
                      'title': title or '',
                      'fields': '\n'.join(fields),

                      # Section describing this form, based on docstring.
                      'about': docstring_html(self.function) or '',

                      # Function name as hidden field so it may trigger the
                      # evaluation of the function upon form submission!
                      'hidden trigger field': ('<input type="hidden" id="{0}"'
                                               'name="{0}" value="true">'
                                               .format(self.name)),
                     }

        return template(FORM, form_parts)

    def evaluate(self, form):

        # If the function name is not in POST/GET, we're providing
        # the HTML input form.
        if form.getvalue(self.name) is None:

            return self.to_form(), None

        # Find corellated arguments in mind. Assume text input,
        # unless noted in arg_map
        arg_values = ([file_or_text(form, arg) for arg in self.args]
                      if self.args else None)
        kwargs = ({k: file_or_text(form, k) for k in self.kwargs}
                   if self.kwargs else None)

        # REQUIRED field missing in POST/GET.
        if None in arg_values:
            missing_args = list()

            for i, value in enumerate(arg_values):

                if value is None:
                    missing_args.append(self.args[i])

            message = ('<p><strong><strong>Error:</strong> missing '
                       'arguments: %s.' % ', '.join(missing_args))

            return message, form

        if arg_values and kwargs:
            evaluation = self.function(*arg_values, **kwargs)
        elif arg_values:
            evaluation = self.function(*arg_values)
        elif kwargs:
            evaluation = self.function(**kwargs)

        # Now we must analyze the evaluation of the function, in order
        # to properly format the results to HTML.

        # ... Evaluation is a string; just use paragraph formatting.
        if isinstance(evaluation, str):

            return paragraphs(evaluation), form

        # ... Evaluation is iterable sequence; further options below...
        elif (isinstance(evaluation, list)
              or isinstance(evaluation, tuple)):

            # Evaluation is an iterable sequence of dictionaries?
            if isinstance(evaluation[0], dict):
                possible_table = iter_dicts_table(evaluation)

                if possible_table:

                    return possible_table, form

        # Evaluation is simply a dictionary! Create a definition list.
        elif isinstance(evaluation, dict):
            pass

        # This SHOULDN'T be possible.
        raise Exception('Unhandled evaluation type!')


def file_or_text(form, form_field):
    """Will return a cgi.fileitem or the corresponding string
    for form_field in form.

    Args:
      form (cgi.FieldStorage): the current cgi field storage
        session.
      form_field (str): grab this field's value.

    Returns:
      str|fileitem: returns string if text field, returns cgi
        module fileitem if a file.

    """

    item = form.getvalue(form_field)

    if item is None:

        return None

    # item is a file
    elif form[form_field].filename:

        # this returns the fileitem
        return form[form_field]

    # item is string or list
    else:

        return item


def funcform(*functions, **kwargs):
    """Just form_handler for multiple functions, while returning
    ONLY the function evaluation on POST/GET.

    Args:
      **kwargs: function_name: dictionary. Dictionary is argument
        to type mapping...

    """

    form = cgi.FieldStorage()
    output = ''

    for function in functions:
        handler = FuncForm(function)
        handler.argument_types = kwargs.get(handler.name, {})
        evaluation, post_get = handler.evaluate(form)

        if post_get:
            back_to_input = ('<form><input type="submit" '
                             'value="Back to Form"></form>')

            return evaluation + back_to_input

        else:
            output += evaluation

    return output

