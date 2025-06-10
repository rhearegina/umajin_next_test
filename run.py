#!/usr/bin/env python3

import sys
import re
import os
import optparse
import shutil


pathname = os.path.dirname(sys.argv[0])
# RHEA: modified to current dir
sys.path.append(os.path.join(pathname, *[ '.','python_modules']))

#print('<sys.path>')
#print(sys.path)

from test_helper import rm_tree, test_suite, write_results, print_results, run_test, prepare_expected_results, prepare_test_script, disable_crash_reporter, enable_crash_reporter, get_test_info, copy_results
import umajin.app

import importlib.machinery

loader = importlib.machinery.SourceFileLoader("test_list", "test_list.py")
test_list = loader.load_module()

#tests_dir = os.path.abspath(os.path.dirname('.'))
tests_dir = 'qatest/'
results_dir = os.path.join(tests_dir, 'results')
normal_test_suite = test_suite('Normal')
# a copy of all the files in the results directory across all tests.
output_dir = os.path.join(tests_dir, "results_output")

# TODO: Delete later
#print("tests_dir:" + tests_dir)
#print("results_dir:" + results_dir)
#print("output_dir:" + output_dir)

parser = optparse.OptionParser(usage='usage: %prog [options]',
                           description='Regression Test Runner')
parser.add_option('-f', '--output-to-file', dest='output_to_file', action='store_true')
parser.add_option('-c', '--config', dest='build_config', type='string')
parser.add_option('-o', '--options', dest='options', type="string", default='',
   help="Comma-seperated list of feature options to enable.")
parser.add_option('-r', '--renderer', dest='render', type='string')
parser.add_option('--use-branch-name',
   dest='use_branch_name', action='store_true',
   help='Use HG branch name as part of build directory name.')
parser.add_option('--test-cli',
   dest='test_cli', action='store_true',
   help='Test CLI JIT instead of GUI.')
parser.add_option('--platform',
   dest='platform', type='string', help='Platform configuration to use.')
(options, args) = parser.parse_args()

opts = '-%s' % '-'.join(options.options.split(',')) if options.options else ''

if len(args) == 0:
   test_cases = test_list.tests_list
   print('no args::')
   print(test_cases)
else:
   test_cases = args

tests = []
for t in test_cases:
   entry = t
   extra_args = []
   if isinstance(t, list):
      extra_args = t[1:]
      t = t[0]
   extension = '.u'
   if (t[-1] == '.'):
      extension = 'u' # This allows tab completion to be used, without having to delete too
   elif (t[-2:] == '.u'):
      extension = ''
   # TODO: Delete prints later
   #testcase_filepath = os.path.abspath(t + extension)
   testcase_filepath = os.path.join(tests_dir, t + extension)
   #print("<run_py> test case filepath:: " + testcase_filepath)
   results_filepath = os.path.splitext(testcase_filepath)[0] + ".txt"
   #print("<run_py> results_filepath filepath:: " + results_filepath)
   tests.append((testcase_filepath, results_filepath, extra_args, entry))

   #print("<run_py> entry:")
   #print(entry)

#print("<run.py> tests:")
#print(tests)

outputter = print_results
if options.output_to_file:
   outputter = write_results

umajin_relative = umajin.app.exe(options.build_config, options.use_branch_name, opts, 'umajin_cli' if options.test_cli else 'umajin', options.platform)

# TODO: Delete prints later
#print("print umajin_relative:")
#print(umajin_relative)

if not umajin_relative:
   print("Umajin exe not found")
   sys.exit(1)

umajin = os.path.abspath(umajin_relative)
umajin_exe = [umajin, '--max-parallel-jobs=1', '--lazy=false', '--log-level=info', '--log-format=l:s', '--log-output=' + ('stderr' if options.test_cli else 'stdout'), '--testing-mode=yes', '--print-jam=none:']

# If a renderer was specified, add it now.
if options.test_cli:
   print ("Using " + umajin)
else:
   if options.render:
      umajin_exe += ['--renderer=' + options.render]
      print( "Using " + umajin + " with renderer: " + options.render )
   else:
      print( "Using " + umajin + " with default renderer" )

# TODO: Delete prints later
#print('<umajin_exe>')
#print(umajin_exe)

disable_crash_reporter(options.platform)

# Make a clean output directory, we will copy the contents
# results into the output_dir before the next test,
# to have a log of all the output.
#print("<run_py>: out_dir: " + output_dir)
if os.path.exists(output_dir):
   rm_tree(output_dir)
os.mkdir(output_dir)

for (test, results, extra_args, entry) in tests:
   # make a clean directory, some tests such as resource system ones want a clean directory.
	# if that's too strict then we can make an extra arg for it or something.
   # TODO: Delete prints later
   #print("<run_py> tests:" + test)
   #print("<run_py> results: " + results)
   #print("<run_py> extra_args: ")
   #print(extra_args)
   #print("<run_py> entry: " + entry)

   if os.path.exists(results_dir):
      rm_tree(results_dir)
   os.mkdir(results_dir)

   #wd = os.path.dirname(os.path.abspath(test))
   wd = os.getcwd()
   #print("wd : " + wd)

   (name, desc) = get_test_info(test)
   #print("test_info: name =" + name)
   #print("test_info: desc =" + desc)

   if os.path.exists(results):
      r = prepare_expected_results(results)
   else:
      r = None
   
   #print("<run.py> expected_result: r =")
   #print(r)

   extra_args_as_string = ''
   if len(extra_args) != 0:
      extra_args_string = " %s" % extra_args
   print ("%s%s: %s" % (name, extra_args_as_string, desc), flush=True)
   f = prepare_test_script(test, results_dir, test)
   
   #print("<run.py> return f =")
   #print(f)
   
   if os.path.isdir("~/Library/Saved Application State/com.umajin.umajin.savedState"):
      try:
         shutil.rmtree("~/Library/Saved Application State/com.umajin.umajin.savedState")
      except OSError as e:
         print("Failed to remove umajin saved state. OS X may prevent umajin running without requiring interaction.")
  
   # TODO: Delete prints later
   # print('<run.py> result_dir::' + results_dir)
   if run_test(umajin_exe + ['--script=%s' % f.name] + extra_args, entry, results_dir, f, 0, r, normal_test_suite, wd):
      print( " - pass" )
   else:
      print( " - fail")

   # copy results into the outputdir, useful for jenkins.
   copy_results(results_dir, output_dir, name)

   #remove the test file
   os.remove(f.name)
      
outputter([normal_test_suite], open(os.path.join(results_dir, 'regression_tests.xml'), 'w+'))

enable_crash_reporter(options.platform)
