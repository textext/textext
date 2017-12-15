"""
This script generates 2 lists of NSIS commands (install&uninstall)
for all files in a given directory

It has been taken from
http://nsis.sourceforge.net/Talk:Uninstall_only_installed_files
and has been slightly modified.
 
Usage:
    gen_list_files_for_nsis.py 
Where
    <dir src>       :   dir with sources; must exist
    <inst list>     :   list of files to install (NSIS syntax)
    <uninst list>   :   list of files to uninstall (NSIS syntax)
                        (both these will be overwriten each time)
"""
import sys, os, glob
 
# global settings
source_dir = 'files/mingw32'
inst_list =  'inst_file_list.txt'
uninst_list = 'uninst_file_list.txt'

just_print_flag = 0 # turn to 1 for debugging
 
# templates for the output
inst_dir_tpl  = '  SetOutPath "$INSTDIR%s"'
inst_file_tpl = '  File "${FILES_SOURCE_PATH}%s"'
uninst_file_tpl = '  Delete "$INSTDIR%s"'
uninst_dir_tpl  = '  RMDir "$INSTDIR%s"'
 

if not os.path.isdir(source_dir):
    print('Directory %s not found!' % (soure_dir))
    sys.exit(1)
 
def open_file_for_writting(filename):
    "return a handle to the file to write to"
    try:
        h = file(filename, "w")
    except:
        print "Problem opening file %s for writting"%filename
        sys.exit(1)
    return h
 
if not just_print_flag:
    ih= open_file_for_writting(inst_list)
    uh= open_file_for_writting(uninst_list)
 
stack_of_visited = []
counter_files = 0
counter_dirs = 0
print "Generating the install & uninstall list of files"
print "  for directory", source_dir
print >> ih,  "  ; Files to install\n"
print >> uh,  "  ; Files and dirs to remove\n"
 
# man page of walk() in Python 2.2  (the new one in 2.4 is easier to use)
 
# os.path.walk(path, visit, arg) 
    #~ Calls the function visit with arguments (arg, dirname, names) for each directory 
    #~ in the directory tree rooted at path (including path itself, if it is a directory). 
    #~ The argument dirname specifies the visited directory, the argument names lists 
    #~ the files in the directory (gotten from os.listdir(dirname)). The visit function 
    #~ may modify names to influence the set of directories visited below dirname, 
    #~ e.g., to avoid visiting certain parts of the tree. (The object referred to by names 
    #~ must be modified in place, using del or slice assignment.) 
 
def my_visitor(my_stack, cur_dir, files_and_dirs):
    "add files to the install list and accumulate files for the uninstall list"
    global counter_dirs, counter_files, stack_of_visited
    counter_dirs += 1
 
    if just_print_flag:
        print "here", my_dir
        return
 
    # first separate files
    my_files = [x for x in files_and_dirs if os.path.isfile(cur_dir+os.sep+x)]
    # and truncate dir name
    my_dir = cur_dir[len(source_dir):]
    if my_dir=="": my_dir = "\\."
 
    # save it for uninstall
    stack_of_visited.append( (my_files, my_dir) )
 
    # build install list
    if len(my_files):
        print >> ih,  inst_dir_tpl % my_dir
        for f in my_files:
            print >> ih,  inst_file_tpl % (my_dir+os.sep+f)
            counter_files += 1
        print >> ih, "  "
 
os.path.walk( source_dir, my_visitor,  stack_of_visited)
ih.close()
print "Install list done"
print "  ", counter_files, "files in", counter_dirs, "dirs"
 
stack_of_visited.reverse()
# Now build the uninstall list
for (my_files, my_dir) in stack_of_visited:
        for f in my_files:
            print >> uh,  uninst_file_tpl % (my_dir+os.sep+f)
        print >> uh, uninst_dir_tpl % my_dir
        print >> uh, "  "
 
# now close everything
uh.close()
print "Uninstall list done. Got to end.\n"