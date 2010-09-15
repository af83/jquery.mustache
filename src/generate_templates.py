"""To Generate a JS file containing mustache templates.
Lines are stripped and lines starting with '##' are ignored.
"""
from __future__ import with_statement
import codecs
import commands
import dircache
import gettext
from optparse import OptionParser
import os
from os.path import sep, abspath
import re

try:
  import json
except ImportError:
  import simplejson as json


TEMPLATES_FILE = 'templates_%s.js'

LANGUAGES = ['fr', 'en', 'es']

# This is the base file used as PO file when none exist
# There is no creation/modification time on purpose
# (I do think this is the (D)VCS job.
TEMPLATE_PO = """
msgid ""
msgstr ""
"Project-Id-Version: templates\\n"
"Report-Msgid-Bugs-To: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""


def extract_strings(templates_dir):
  """Run commands to extract wordings (generate/update po/mo files in i18n).
  """
  for lang in LANGUAGES:
    data = dict(lang=lang, base_dir = templates_dir)

    data['po_file'] = po_file = "%(base_dir)s/i18n/templates_%(lang)s.po" % data
    if not os.path.exists(po_file): 
      with open(po_file, 'w') as f:
        f.write(TEMPLATE_PO)

    cmd = ("xgettext -j -L Python --from-code=utf-8 "
           "--omit-header "
           "--force-po "
           "--package-name=templates "
           "-o %(po_file)s "
           "--force-po "
           "%(base_dir)s/*.ms") % data
    print cmd
    status, output = commands.getstatusoutput(cmd)
    if status != 0:
      print output
      raise AssertionError("Bad returned value from: " + cmd)
    data['destination'] = '%(base_dir)s/i18n/build/%(lang)s/LC_MESSAGES' % data
    cmd2 = ('mkdir -p %(destination)s && '
            'msgfmt -o %(destination)s/templates.mo '
            '%(base_dir)s/i18n/templates_%(lang)s.po') % data
    print cmd2
    status, output = commands.getstatusoutput(cmd2)    
    if status != 0:
      print output
      raise AssertionError("Bad returned value from: " + cmd2)



trans_re = re.compile('''_\("(.*?)"\)''')
def transform_line(line, t):
   """Returns transformed line: translations + strip.
   """
   line = line.strip()
   if line.startswith('##'): return ''
   for group in trans_re.findall(line):
     line = line.replace('_("%s")' % group, t.gettext(group))
   return line



def get_js_templates(templates_dir, lang):
  """Returns a JS string (hash) containing all the Mustache templates.
  """
  t = gettext.translation('templates', '%s/i18n/build' % templates_dir, 
                          languages=[lang])
  names = [name for name in dircache.listdir(templates_dir)
           if name.endswith('.ms')]
  templates = {}
  for name in names:
    fname = "%s/%s" % (templates_dir, name)
    name = name[:-3]
    with codecs.open(fname, encoding="utf8") as templatef:
      lines = [transform_line(l, t) for l in templatef]
      templates[name] = "".join(lines)
  res = json.dumps(templates)
  return res


def gen_template_file(templates_dir, lang):
  """Generate a templates files for a given language.

  Arguments:
    - templates_dir: path where are located all the templating files.
    - lang: string, "fr", "en"...
  """
  json_templates = get_js_templates(templates_dir, lang)
  fpath = '%s/build/%s' % (templates_dir, TEMPLATES_FILE % lang)
  with open(fpath, 'w') as tf:
    tf.write('''
;(function($) {
  var TEMPLATES = %s;
  $.fn.renders = function(template_name, data) {
    var template = TEMPLATES[template_name];
    if(!template) throw new Error('Undefined template: ' + template_name);
    return $(this).html(Mustache.to_html(template, data || {}, TEMPLATES));
  };
})(jQuery);
    ''' % json_templates)
  print "Generate template file %s." % fpath


def main(ms_dir=None):
  """Extract i18n string + generate templates files.

  Arguments:
    - ms_dir: the directory path where are the templates located. If none given
      will be the directory where the script is located.
  """
  ms_dir = ms_dir or abspath(sep.join(__file__.split(sep)[:-1]))
  if ms_dir.endswith('/'): ms_dir = ms_dir[:-1]
  
  i18n = os.path.join(ms_dir, 'i18n')
  if not os.path.exists(i18n): os.makedirs(i18n)

  extract_strings(ms_dir)
  for lang in ['en', 'fr', 'es']:
    gen_template_file(ms_dir, lang)
  print "Done."


if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-d", "--msdir", dest="msdir",
                    help="Generate templates files from templates in given DIR",
                    metavar="DIR")
  options, args = parser.parse_args()
  main(options.msdir)

