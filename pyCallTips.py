'''
	PythonCallTips  0.7
    (C) Copyright 2004 by tocer deng   MAIL: write2tocer@homtmail.com
					
	This script simualate code calltips in a new bottow window of Vim.
    In fact, it display python help doc strings of word under the cursor
    by scanning the imported modules and functions in the current file.

    It require Python and Vim compiled with "+python" 
    and MAKE SURE "set iskeyword+=."
    
    It work well in my box in Win2000 + Vim6.3 + python2.3. 
    It can also work in GNU/Linux.
    If it can work in other platform or other version of Vim, let me know.
    Note: as I know, Vim6.2 come into conflict with Python2.3, becase Vim6.2
          is compiled with Python2.1. you can update vim version to 6.3.
          Maybe yours not.
          
	Install:
        1. putting below the sentence into your "vimrc" file.
           (in linux, '/' instead of '\\'). So once you open a python file, the 
           script begin running. (SUGGESTION)
           
           autocmd FileType python pyfile <PATH>\\pyCallTips.py
           
           note:<PATH> is the path of pyCallTips.py.
           
        2. Or opening a python file you requied, and execute:
             
             :pyfile <PATH> pyCallTips.py
             
        Notes: 
           1. It split a new little window in the bottom in Vim when the script
              begin running. This is the python calltips windows.
           2. DO NOT "close" the window, otherwise it can't work.
            
     Usage: coding and coding and nothing:)
            
        1. Once you type new "import xxx" or "from xxx import yyy" or other 
           evaluation statement, you MUST press "F4" key. I call it
           "refresh key". This key tell the script read the whole file again
           to get modules and methods. Otherwise the calltips don't be display.

           Note: from 0.7, the script can refresh  automatic if you don't
                 press any key until beyond 5 seconds in the "normal" mode in 
                 Vim. And the time setting is in LINE 393
            
        2. Except "F4", the script also remap five keys: <Alt-1> ... <Alt-5> as
           "auto complete key". As you know, Vim use <Ctrl-N> and <Ctrl-P> to 
           complete word automatically. But when you input word like 
           "module.method(xxx).y", you wish Vim could complete the rest part the
           word automatically. In fatc, the Vim can't.(I have think for a long 
           time, but still don't know how to do. If you know, tell me,thanks)
           So, I deside to remap other keys to complete word automatically.
           using <Alt-1> ... <Alt-5> key to select which one to complete from
           calltips window. If you still don't see, try it yourself.
           
        3. If you want to pause this script, type:
             :py CT_unmapkeys()
           Remember: DO NOT "close" the calltips window.
           
           If you want to resume this script, type:
             :py CT_mapkeys()

        4. If the keys that the script remap come into conflict with yours,
           you can change the key mapping in this file as desired.

	TODO: 
        1. Add map key to close and open calltips window.

    THANKS:
        montumba, Guilherme Salgado

    English is not my native language, so there may be many mistakes of expression.
    If you have any question, feel free to mail to write2tocer@homtmail.com
    If you enjoy it, mail me too, I'm happy to share your joy.
'''

import vim
import __builtin__
from string import letters
try:
    from sets import Set
except:
    pass

def CT_GetWordUnderCursor():
    """ Returns word under the current buffer's cursor."""
    stack = []
    leftword = rightword = popword = word = ''
    WORD = vim.eval('expand("<cWORD>")')  #return a big WORD

    #According '.', seperate the WORD into left part and right part
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
    #print word

    return word

def CT_AutoComplete(index):
    """Return matched word in calltip window"""
    try:
        #get first field of index line of helpBuffer
        if helpBuffer[index-1].find('__builtin__') == 0:  #see if builtin function
            autoPart = helpBuffer[index-1].split()[0][len(CT_GetWordUnderCursor())+12:]  #11: len('__biultin__.')
        else:
            autoPart = helpBuffer[index-1].split()[0][len(CT_GetWordUnderCursor()):]
        vim.command('execute "normal a' + autoPart + '"')
    except:
        #print "auto complete ERROR"
        pass
    vim.command('startinsert!')   #from normal mode into insert mode
    #print autoPart

def CT_GetHelp(word):   
    """Return module or methods's  doc strings."""
    
    helpDoc = []
    spacing=16
    if len(word.split('.')) == 1:      #see if type "xxx."
        s = '__builtin__'
        m = word
    else:
        rindex= word.rfind('.')        #see if type "xxx.xx"
        s = word[:rindex]
        y, x = vim.current.window.cursor
        m = word[rindex+1:x+1]
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

def CT_ImportObject():
    """Import modules and function in the file"""            
    import tokenize
    import keyword
    import StringIO
    import pywin.debugger
    text='\n'.join(vim.current.buffer[:]) + '\n'
    f = StringIO.StringIO(text)
    g = tokenize.generate_tokens(f.readline)
    lineNo = 0
    for tokenType, t, start, end, line in g:
        if start[0] == lineNo: continue
        if tokenType == tokenize.INDENT or tokenType == tokenize.DEDENT \
                 or tokenize.tok_name[tokenType] == 'NL' \
                 or tokenType == tokenize.ERRORTOKEN \
                 or tokenType == tokenize.ENDMARKER \
                 or start[0] == lineNo: continue
        if t == 'import':
            module = ''
            while 1:
                tokenType, t, start, end, line = g.next()
                if t == ';' or tokenType == tokenize.NEWLINE:
                    try:
                        exec('import %s' % module) in globals()
                    except: 
                        print "Ignore: can't import %s\n" % module
                    break
                elif (tokenType == tokenize.OP and t == ','):
                    try:
                        exec('import %s' % module) in globals()
                    except: 
                        print "Ignore: can't import %s\n" % module
                    module = ''
                    continue
                module += t + ' '
        elif t == 'from':
            module = ''
            while 1:
                tokenType, t, start, end, line = g.next()
                if t == 'import': break
                module += t
            function = ''
            while 1:
                tokenType, t, start, end, line = g.next()
                if  t == ',':
                    try:
                        exec('from %s import %s' % (module, function)) in globals()
                    except:
                        print "Ignore: can't from %s import %s\n" % (module, function)
                    function = ''
                    continue
                elif tokenType == tokenize.NEWLINE:
                    try:
                        exec('from %s import %s' % (module, function)) in globals()
                    except: 
                        print "Ignore: can't from %s import %s\n" % (module, function)
                    break
                function += t + ' '
        
        elif t == 'class':
            i = 0
            l = 'class '
            classBlock = []
            while 1:
                tokenType, t, start, end, line = g.next()
                if tokenType == tokenize.INDENT:
                    i += 1
                    l = ' '*i*4
                elif tokenType == tokenize.DEDENT:
                    i -= 1
                    l = ' '*i*4
                    if i == 0: break
                elif tokenType == tokenize.NEWLINE or\
                         tokenType == tokenize.NL      or\
                         tokenType == tokenize.COMMENT:
                    classBlock.append(l)
                    l = ' '*i*4
                else:
                    l += t + ' '
            #print "class: %s" % classBlock[0]
            try:
                exec('\n'.join(classBlock)+'\n') in globals()
            except: pass
                #print "Ignore: can't import %s" % classBlock[0]
        elif keyword.iskeyword(t):
            lineNo = start[0]
        else:
            if t in globals():
                lineNo = start[0]
                continue
            varName = t
            tokenType, t, start, end, line = g.next()
            if t == '=':
                tokenType, t, start, end, line = g.next()
                if tokenType == tokenize.NEWLINE: break
                elif t == 'helpBuffer': pass
                #see if vars ='xxx' or "xxx" or '''xxx''' or """xxx""" or str(xxx)
                elif tokenType == tokenize.STRING or t == 'str':  
                    #print 'sting:%s' % varName
                    exec('%s = CT_STRINGTYPE' % varName)  in globals()
                #see if vars = [] or list()
                elif t == '[' or t == 'list':
                    #print 'list:%s' % varName
                    exec('%s= CT_LISTTYPE' % varName)  in globals()
                #see if vars = {} or dict()
                elif t == '{' or t == 'dict':
                    #print 'dict:%s' % varName
                    exec('%s = CT_DICTTYPE' % varName)  in globals()
                #see if vars = NUMBER
                elif tokenType == tokenize.NUMBER:
                    pass
                    #print 'number:%s' % varName
                #see if vars = Set([xxx])
                elif t == 'Set': 
                    #print 'set:%s' % varName
                    try:
                        exec('%s = CT_SETTYPE' % varName)  in globals()
                    except:
                        pass
                #see if vars = open(xxx) or file(xxx)
                elif t == 'open' or t == 'file':
                    #print 'file:%s' % varName
                    exec('%s = CT_FILETYPE' % varName)  in globals()
                else:
                    instance = t
                    #pywin.debugger.set_trace()
                    while 1:
                        tokenType, t, start, end, line = g.next()
                        if tokenType == tokenize.NAME and t == '.':
                            instance += t
                        elif tokenType == tokenize.NEWLINE: break
                        else:
                            #print 'instance: %s' % line
                            try:
                                exec('%s = %s' % (varName, instance))  in globals()
                            except: pass
                                #print 'ERROR: %s = %s' % (varName, instance)  
                            break
            lineNo = start[0]
    return 

def CT_CallTips():
    """Display help doc string in Python calltips buffer"""
    helpBuffer[:] = None
    docs = CT_GetHelp(CT_GetWordUnderCursor())

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
        
def CT_mapkeys():
    """mapping keys"""
    #mapping "a-zA-Z." keys
    for letter in letters+'.':    
        vim.command("inoremap <buffer> %s %s<Esc>:python CT_CallTips()<CR>" \
                    % (letter, letter))
    #mapping "Back Space" keys
    vim.command("inoremap <buffer> <BS> <BS><Esc>:python CT_CallTips()<CR>")
    #mapping "F4" keys
    vim.command("inoremap <buffer> <F4> <Esc>:python CT_ImportObject()<CR>")
    #mapping "Alt 1" key
    vim.command("inoremap <buffer> <M-1> <Esc>:python CT_AutoComplete(1)<CR>")
    #mapping "Alt 2" key
    vim.command("inoremap <buffer> <M-2> <Esc>:python CT_AutoComplete(2)<CR>")
    #mapping "Alt 3" key
    vim.command("inoremap <buffer> <M-3> <Esc>:python CT_AutoComplete(3)<CR>")
    #mapping "Alt 4" key
    vim.command("inoremap <buffer> <M-4> <Esc>:python CT_AutoComplete(4)<CR>")
    #mapping "Alt 5" key
    vim.command("inoremap <buffer> <M-5> <Esc>:python CT_AutoComplete(5)<CR>")

def CT_unmapkeys():
    """unmapping keys"""
    try:
        #Unmapping "a-zA-Z." keys
        for letter in letters+'.':    
            vim.command('iunmap <buffer> %s' % letter)
        #Unmapping "Back Space" keys
        vim.command('iunmap <buffer> <BS>')
        #Unmapping "F4" keys
        vim.command('iunmap <buffer> <F4>')
        #Unmapping "Alt 1" key
        vim.command('iunmap <buffer> <M-1>')
        #Unmapping "Alt 2" key
        vim.command('iunmap <buffer> <M-2>')
        #Unmapping "Alt 3" key
        vim.command('iunmap <buffer> <M-3>')
        #Unmapping "Alt 4" key
        vim.command('iunmap <buffer> <M-4>')
        #Unmapping "Alt 5" key
        vim.command('iunmap <buffer> <M-5>')
    except:
        pass

def CT_Init():
    """creat a new calltips windows"""

    global helpBuffer
    vim.command('silent botright new Python_CallTips')
    vim.command('set buftype=nofile')
    vim.command('set nonumber')
    vim.command('resize 5')
    vim.command('set noswapfile')
    helpBuffer = vim.current.buffer
    vim.command('wincmd p')   #switch back window
    vim.command('autocmd CursorHold *.py python CT_ImportObject()')
    vim.command('set updatetime=5000')
    from sys import path
    path.extend(['.','..'])  #add current path and parent path

def CT_Init2():
    """clear calltips buffer and unused python object"""

    ALL = ['CT_GetWordUnderCursor', 'CT_AutoComplete', 'CT_GetHelp',\
           'CT_ImportObject', 'CT_CallTips', 'CT_mapkeys', 'CT_unmapkeys',\
           'CT_Init', 'CT_Init2', '__builtin__', '__builtins__', '__doc__', \
           '__name__', 'vim', 'letters', 'helpBuffer', 'CT_STRINGTYPE', \
           'CT_LISTTYPE', 'CT_DICTTYPE', 'CT_FILETYPE', 'CT_SETTYPE', 'Set']
    helpBuffer[:] = None  #clear help buffer
    
    for object in globals().keys():
        if object not in ALL:
            try:
                exec('del %s' % object) in globals()
            except: pass
                #print 'Fail: del %s' % object
        

#VERBOSE = False
#VERBOSE = True           #inter method is displayed, such as '__str__','__repr__' etc.

CT_STRINGTYPE = str
CT_LISTTYPE   = list
CT_DICTTYPE   = dict
CT_FILETYPE   = file
CT_SETTYPE    = Set

if 'helpBuffer' in dir():
    CT_Init2()
    CT_ImportObject()
else:
    CT_Init()            
    CT_mapkeys()         
    CT_ImportObject()    
