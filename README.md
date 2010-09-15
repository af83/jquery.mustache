# jquery.mustache
A JQuery plugin to ease the use of Mustache templates

## Goal

jquery.mustache let you write your Mustache templates in plain text files and
then combine them in one JS file (a jQuery plugin) making it easy to render your 
templates.


## Example

### The template "banner" in the file "banner.ms":
    ## This is a comment line and will be ignored
    <div class="banner">
      Welcome to my site {{user}}!
      <ul class="menu">
        <li><a href="#page1">Page1</a></li>
        <li><a href="#page2">Page2</a></li>
      </ul>
    </div>

### The template "page1" in the file "page1.ms":
    {{>banner}}
    <div class="page">
      <p>_("This is a i18n text of the page 1")</p>
    </div>

### The template "page2" in the file "page2.ms":
    {{>banner}}
    <div class="page">
      <p>_("This is a i18n text of the page 2")</p>
    </div>

### How you can render these templates in your JS code:
    $('body').renders('page1', {
      user: "Chuck Norris"
    });


You don't have to specify your partials, you can use whatever template
name you have written (here "banner").


## How it works
jquery.mustache features a python script which you run once you have written 
or updated your templates files. This script generates one or more files named
as template_en.js (for english version here) plus generate/update i18n (po/mo) 
files using xgettext / msgfmt.

You include the generated file in your page as a regular js file, and then you
can use the "renders" function on jQuery elements!

The generated file looks like:

    ;(function($) {
      var TEMPLATES = {"banner": "<div class=\"banner\">...</div>", "page1": "...", "page2": "..."};
      $.fn.renders = function(template_name, data) {
        var template = TEMPLATES[template_name];
        if(!template) throw new Error('Undefined template: ' + template_name);
        return $(this).html(Mustache.to_html(template, data || {}, TEMPLATES));
      };
    })(jQuery);

You can see a working example in the example directory.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see [http://www.fsf.org/licensing/licenses/agpl-3.0.html](http://www.fsf.org/licensing/licenses/agpl-3.0.html)

