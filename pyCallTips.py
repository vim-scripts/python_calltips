"""
	PythonCallTips  0.3
	(C) Copyright 2004 by tocer deng dm-info@163.com
					

	In a new bottow window, display help doc strings of word under
    the cursor by scanning the modules in the current file.

    It requier Vim compiled with "+python and MUST set iskeyword+=. ".
    
    It work well in my box in Win2000 and Vim6.3. If it work in other 
    platform or other version of Vim, let me know.
    
	Usage: 
        1.  open a python file, and execute:
             :pyfile <PATH> pyCallTips.py
            of cource be sure Vim can find it. the call tip would by displayed
            in the bottom window.
            Or put the command into .vimrc to autorun
        2.  if you input new "import xxx" or "from xxx import yyy" statement,
            you would press "F4" key to refresh it. Do it only, the new module's 
            calltips can be displayed.
		3.  You can change the key mapping at the bottom of this file as desired.

	TODO: 1.Read a Vim's WORD, and pick up right form
            e.g. "helpBuffer[1].append" --> "helpBuffer.append" 
          2.Declare variable as object in the comment, so analyzing it,
            and  import the object. Then sequence and dictionay's methed 
            help doc string could be display.

    English is not my native language, so there may be many mistake of expression.
    if you have any question, please mail to dm-info AT 163.COM
    Welcom to fix bug:)
"""

import vim
import __builtin__
from string import letters

def GetWordUnderCursor():
    """ Returns word under the current buffer's cursor.
    """
    return vim.eval('expand("<cword>")') 

def GetHelp(word):   
    '''Get methods's  doc strings.'''
    
    helpDoc = []
    spacing=16
    if len(word.split('.')) == 1:
        s = '__builtin__'
        m = word
    else:
        rindex= word.rfind('.')
        s = word[:rindex]
        m = word[rindex+1:]
    try:
        object = eval(s)
    except:
        return []
    joinLineFunc = lambda s: " ".join(s.split())

    methodList = [method for method in dir(object) \
                         if method.find('__') != 0 and \
                            method.find(m) == 0    and \
                            '__doc__' in dir(getattr(object, method))]
    helpDoc.extend(["%s.%s %s" %
                    (s,method.ljust(spacing),
                     joinLineFunc(str(getattr(object, method).__doc__)))
                     for method in methodList])
    return helpDoc

def ImportObject():
    '''Check module and function in whole current buffer,
       and import it.
    '''            
    importList = []
    for line in vim.current.buffer:
        words = line.split()
        if len(words) > 0 and (words[0] == 'import' or words[0] == 'from'):
            try:
                exec(line.strip())  in globals()
            except:
                print "Error import : %s" % line
    return 

def CallTips():
    '''Display help doc string in Python help buffer
    '''
    helpBuffer[:] = None
    docs = GetHelp(GetWordUnderCursor())

    #print docs
    for line in docs:
        helpBuffer.append(line)
    del helpBuffer[0]

    y, x = vim.current.window.cursor
    if len(vim.current.line) > x + 1:
        vim.command('normal l')
        vim.command('startinsert')
    else:
        vim.command('startinsert!')
        

if 'helpBuffer' in dir():
        helpBuffer[:] = None  #clear help buffer
else:
    vim.command("silent botright new Python help")
    vim.command("set buftype=nofile")
    vim.command("set nonumber")
    vim.command("resize 5")
    helpBuffer = vim.current.buffer
    vim.command("wincmd p")   #switch back window
#mapping "a-zA-Z." keys
for letter in letters+'.':    
    vim.command("inoremap <buffer> %s %s<Esc>:python CallTips()<CR>" \
                % (letter, letter))
#mapping "Back Space" keys
vim.command("inoremap <buffer> <BS> <BS><Esc>:python CallTips()<CR>")

#mapping "F4" keys
vim.command("inoremap <buffer> <F4> <Esc>:python ImportObject()<CR>")
ImportObject()
