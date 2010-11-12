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
import sys

try:
  import json
except ImportError:
  import simplejson as json


TEMPLATES_FILE = 'templates_%s.js'


# This is the base file used as PO file when none exist
# There is no creation/modification time on purpose
# (I do think this is the (D)VCS job.
TEMPLATE_PO = """
msgid ""
msgstr ""
"Project-Id-Version: templates\\n"
"Report-Msgid-Bugs-To: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""


def extract_strings(templates_dir, languages, update_mo=True):
  """Run commands to extract wordings (generate/update po/mo files in i18n).

  Arguments:
    - templates_dir: where are located the templates files.
    - languages: list of strings, languages to generate templates in.
      Example: ['en', 'fr', 'es']
    - update_mo, optional boolean, default to True, if False then don't 
      (re)generate the mo files.
  """
  for lang in languages:
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
    if not update_mo: continue
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
     group_utf8 = group.encode('utf-8')
     replacement = t.gettext(group_utf8)
     if replacement == group_utf8: replacement = group
     else: replacement = replacement.decode('utf-8')
     line = line.replace('_("%s")' % group, replacement)
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


def gen_template_file(templates_dir, lang, output_dir):
  """Generate a templates file for a given language.

  Arguments:
    - templates_dir: path where are located all the templating files.
    - lang: string, "fr", "en"...
    - output_dir: path of the dir where should be put the generated file.

  """
  json_templates = get_js_templates(templates_dir, lang)
  fpath = '%s/%s' % (output_dir, TEMPLATES_FILE % lang)
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


def main(languages, ms_dir=None, i18n_extraction=True, output_dir=None, 
         only_extract_str=False):
  """Extract i18n string + generate templates files.

  Arguments:
    - ms_dir: the directory path where are the templates located. If none given
      will be the directory where the script is located.
    - languages: list of strings, languages to generate templates in.
      Example: ['en', 'fr', 'es']
    - i18n_extraction: bool, if false don't create/update po/mo files.
      This will have for effect only to update generated js templates files 
      without touching at translations.
    - output_dir: path of the dir where should be put the generated file.
      If None, will be in 'build' directory, within templates dir.
    - only_extract_str: boolean, default to False. If set to True, then
      the strings are extracted for i18n (in po files), but nothing else is
      done. This option cannot be True in the same time i18n_extraction is
      set to false.

  """
  if not i18n_extraction and only_extract_str:
    raise AssertionError('You cannot have i18n_extraction==False and'
                         'only_extract_str==True.')
  ms_dir = ms_dir or abspath(sep.join(__file__.split(sep)[:-1]))
  if ms_dir.endswith('/'): ms_dir = ms_dir[:-1]
  if output_dir is None: output_dir = '%s/build' % ms_dir
  
  i18n = os.path.join(ms_dir, 'i18n')
  if not os.path.exists(i18n): os.makedirs(i18n)

  if only_extract_str:
    extract_strings(ms_dir, languages, update_mo=False)
  else:
    if i18n_extraction:
      extract_strings(ms_dir, languages)
    for lang in languages:
      gen_template_file(ms_dir, lang, output_dir)
  print "Done."


if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("-d", "--msdir", dest="msdir",
                    help="Generate templates files from templates in given DIR",
                    metavar="DIR")
  parser.add_option("-l", "--languages", dest="languages", default="en,fr,es",
                    help="Specify the languages you want. Ex: en,fr,de")
  parser.add_option("-s", "--skipi18n", dest="i18n_extraction", default=True,
                    action="store_false",
                    help=("Skip po/mo files update/creation process. "
                          "For this to work, you need to have the po files "
                          "of the requested languages (even if empty). "
                          "Cannot be ran with -X option.")
                    )
  parser.add_option('-X', '--onlyXtractStrings', dest='onlyXtractStrs', 
                    default=False, action="store_true",
                    help=("Only extract templates strings for i18n. "
                          "No template is (re)generated, no MO file "
                          "is produced (only po files). "
                          "Cannot be ran with -S option.")
                    )
  parser.add_option("-o", "--output", dest="out_dir", default=None,
                    metavar="DIR",
                    help="Path to the directory where to put generated files.")
  options, args = parser.parse_args()
  if not options.msdir or not options.out_dir:
    print ('The options -o and -d are not optional (even if called options!).')
    sys.exit(1)
  if not options.i18n_extraction and options.onlyXtractStrs:
    print ('--skipi18n (-s) and --onlyXtractStrings (-X) are mutually exclusive'
           ' and cannot be used silmutaneously.')
    sys.exit(1)
  languages = options.languages.split(',')
  main(languages, options.msdir, options.i18n_extraction, options.out_dir,
       options.onlyXtractStrs)

