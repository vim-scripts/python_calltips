'''
	PythonCallTips  0.5
    (C) Copyright 2004 by tocer deng   MAIL: write2tocer@homtmail.com
					
	This script simualate code calltips in a new bottow window of Vim.
    In fact, it display python help doc strings of word under the cursor
    by scanning the imported modules in the current file.

    It require Python and Vim compiled with "+python" 
    and MAKE SURE "set iskeyword+=."
    
    It work well in my box in Win2000 + Vim6.3 + python2.3. 
    If it can work in other platform or other version of Vim, let me know.
    Note: as I know, Vim6.2 come into conflict with Python2.3, becase Vim6.2
          is compiled with Python2.1. you can update vim version to 6.3.
          Maybe yours not.
          
	Install:
        1. The easiest method is that throwing it into path $VIRUNTIME/plugin.
        2. the easier method is that putting below the sentence into "vimrc" file.
           (in linux, '/' instead of '\\'). So once you open a python file, the 
           script begin running. (SUGGESTION)
           
           autocmd FileType python pyfile <PATH>\\pyCallTips.py
           
           note:<PATH> is the path of pyCallTips.py.
           
        3. Or opening a python file you requied, and execute:
             
             :pyfile <PATH> pyCallTips.py
             
        Notes: 
           1. It split a new little window in the bottom in Vim when the script
              begin running. This is the python calltips windows.
           2. DO NOT "close" the window, otherwise it can't work.
            
     Usage: coding and coding and nothing:)
            
        1. Once you type new "import xxx" or "from xxx import yyy" statement,
           you MUST press "F4" key. I call it "refresh key". This key tell the
           script read the whole file again to get modules and methods.
           Otherwise the calltips don't be display.
            
        2. Except "F4", the script also remap five keys: <Alt-1> ... <Alt-5> as
           "auto complete key". As you know, Vim use <Ctrl-N> and <Ctrl-P> to 
           complete word automatically. But when you input word like 
           "module.method(xxx).y", you wish Vim could complete the rest part the
           word automatically. In fatc, the Vim can't.(I have think for a long 
           time, but still don't know how to do. If you know, mail to me,thanks)
           So, I deside to remap other keys to complete word automatically.
           using <Alt-1> ... <Alt-5> key to select which one to complete from
           calltips window. If you still don't see, try it yourself.
        3. If the keys that the script remap come into conflict with yours,
           you can change the key mapping in this file as desired.

	TODO: 
        1. Make all builtin object type display its calltips.
           I think declare them in somewhere, and analyzing them.
           
        2. If a method evaluate to a variable, it should display calltips also.
        
        3. Solve <Ctrl-N> <Ctrl-P>can't complete automatically. see below.
           But it's urgent.

        4. Probably it extend other function, even language like python. 
           But I know python only now. Maybe you can do it:)

    DEBUG:
          1. The script don't know which one a variable is:
             list, dict, tuple or stings

    English is not my native language, so there may be many mistakes of expression.
    If you have any question, feel free to mail to write2tocer@homtmail.com
    If you enjoy it, mail me too, tell me where are you from if you don't mind.
    I'm happy to share your joy.
'''

import vim
import __builtin__
from string import letters
from sys import path

def __GetWordUnderCursor():
    """ Returns word under the current buffer's cursor.
    """
    stack = []
    leftword = rightword = popword = word = ''
    WORD = vim.eval('expand("<cWORD>")')  #return a big WORD

    #seperate the WORD into left part and right part
    rindex = WORD.rfind('.')
    if rindex == -1:      #if a WORD is not include '.'
        leftWORD = ''
        rightWORD = WORD
    else:
        leftWORD = WORD[:rindex]        
        rightWORD = WORD[rindex+1:]
    #print "WORD=%s, leftWORD=%s rightWORD=%s" % (WORD, leftWORD, rightWORD)

    #analyzing left part of the WORD
    for char in leftWORD:
        if char in letters + '.':
            popword += char
            continue
        elif char == '(' or char == '[':
            stack.append(popword)
            popword = ''
            continue
        elif char == ')' or char == ']':
            leftword=stack.pop()
            popword = ''
            continue
        else:
            popword = ''
    if popword != '': leftword = popword  
    #print "leftword=%s" % leftword

    #analyzing right part of the WORD
    for char in rightWORD:
        if char not in letters:
            break
        rightword += char
    #print "rightword=%s" % rightword
    
    if leftword != '':
        word = "%s.%s" % (leftword, rightword)
    else:
        word = rightword
    print word

    return word

def AutoComplete(index):
    try:
        #get first field of index line of helpBuffer
        if helpBuffer[index-1].find('__builtin__') == 0:  #see if builtin function
            autoPart = helpBuffer[index-1].split()[0][len(__GetWordUnderCursor())+12:]  #11: len('__biultin__.')
        else:
            autoPart = helpBuffer[index-1].split()[0][len(__GetWordUnderCursor()):]
        vim.command('execute "normal a' + autoPart + '"')
    except:
        #print "auto complete ERROR"
        pass
    vim.command('startinsert!')   #from normal mode into insert mode
    #print autoPart

def __GetHelp(word):   
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
    '''Display help doc string in Python calltips buffer
    '''
    helpBuffer[:] = None
    docs = __GetHelp(__GetWordUnderCursor())

    #print docs
    for line in docs:
        helpBuffer.append(line)
    del helpBuffer[0]

    #from normal mode into insert mode
    y, x = vim.current.window.cursor
    if len(vim.current.line) > x + 1:
        vim.command('normal l')
        vim.command('startinsert')
    else:
        vim.command('startinsert!')
        

if 'helpBuffer' in dir():
        helpBuffer[:] = None  #clear help buffer
        ImportObject()
else:
    vim.command("silent botright new Python CallTips Windows")
    vim.command("set buftype=nofile")
    vim.command("set nonumber")
    vim.command("resize 5")
    vim.command("set noswapfile")
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

    #mapping "Alt 1" key
    vim.command("inoremap <buffer> <M-1> <Esc>:python AutoComplete(1)<CR>")

    #mapping "Alt 2" key
    vim.command("inoremap <buffer> <M-2> <Esc>:python AutoComplete(2)<CR>")

    #mapping "Alt 3" key
    vim.command("inoremap <buffer> <M-3> <Esc>:python AutoComplete(3)<CR>")

    #mapping "Alt 4" key
    vim.command("inoremap <buffer> <M-4> <Esc>:python AutoComplete(4)<CR>")

    #mapping "Alt 5" key
    vim.command("inoremap <buffer> <M-5> <Esc>:python AutoComplete(5)<CR>")

    path.extend(['.','..'])  #add current path and parent path
    del path, letter

    ImportObject()
