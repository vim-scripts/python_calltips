" vim: ai et ts=4 sw=4 tw=78:
"PythonCallTips  0.85
"    (C) Copyright 2004 by tocer deng   MAIL: write2tocer@homtmail.com
"
"    This script simualate code calltips in a new bottow window of Vim.
"    In fact, it display python help doc strings of word under the cursor
"    by scanning the imported modules and functions in the current file.
"
"    It require Python and Vim compiled with "+python" 
"    and MAKE SURE "set iskeyword+=."
"    
"    It work well in my box in Win2000 + Vim6.3 + python2.3. 
"    It can also work in GNU/Linux.
"    If it can work in other platform or other version of Vim, let me know.
"    Note: as I know, Vim6.2 come into conflict with Python2.3, becase Vim6.2
"          is compiled with Python2.1. you can update vim version to 6.3.
"          Maybe yours not.
"          
"    Install:
"           Putting the plugin into "$VIMRUNTIME/ftplugin" fold
"           
"    Usage: 
"        1. If there is a menu in Vim, you can start it with clicking menu 
"           "Tools\Start Calltips", and stop it whih menu "Tools\End calltips"
"
"        2. If there is NOT a menu, you can start it with typping:
"             :call DoCalltips()
"           And stop it with
"             :call EndCalltips()
"
"        3. If the plugin is running, you can see change in calltips window 
"           when you type word.
"           
"        4. Once you type new "import xxx" or "from xxx import yyy" or other 
"           evaluation statement, you MUST press "F4" key. I call it
"           "refresh key". This key tell the script read the whole file again
"           to get modules and methods. Otherwise the calltips don't be display.
"
"           Note: from 0.7, the script can refresh  automatic if you don't
"                 press any key until beyond 5 seconds in the "normal" mode in 
"                 Vim. And the time setting is in LINE 453
"            
"        5. The plugin can also implement complete word automatically. I think it 
"           better than pyDiction plugin. When calltips are displayed in calltips window,
"           you can press keys: <Alt-1> ... <Alt-5> to select calltip you want.  
"           If you still don't understand, try it yourself.
"           
"    TODO: Support to auto display calltip when you press "." key without press "F4"
"          in "insert" mode of Vim.
"          
"    THANKS:
"        montumba, Guilherme Salgado, Staale Flock
"
"    English is not my native language, so there may be many mistakes of expression.
"    If you have any question, feel free to mail to write2tocer@homtmail.com
"    If you enjoy it, mail me too, I'm happy to share your joy.

if exists("s:DoCalltips")
    echo "Loaded already"
    finish
else
    echo "Loading python_calltips"
    let s:DoCalltips=0
    let s:MenuBuildt=0
    let g:PTC_AllFiles=0        "If =1  calltips is enabled in all files
endif



func! <SID>SetEventHooks()
    "Use augroup to make shure the autocommand is not nested
    augroup PythonCallTips
        " Remove previous definitions for this group
        au!
        " These Eventhooks does not make any meaning if the file is not a 
        " python file. But the user might consider it otherwise
        "echo 'g:PTC_AllFiles:'.g:PTC_AllFiles
        if (g:PTC_AllFiles == '1') || &filetype == "python"
            au BufEnter * :call <SID>BuildMenu()
            au BufLeave * :call <SID>TearDownMenu()
        endif
    augroup END
endfunc

func! <SID>DoCalltips()
    if s:DoCalltips == 0
        execute "python CT_Init()"            
        execute "python CT_mapkeys()"         
        execute "python CT_ImportObject()" 
    endif
    let s:DoCalltips = 1
endfunc

func! <SID>EndCalltips()
     if s:DoCalltips == 1    
        execute "python CT_Clear()"            
        execute "python CT_unmapkeys()"         
    endif
    let s:DoCalltips = 0
endfunc


func! <SID>BuildMenu()
" Build menu when we enter filtype=python    
    if has("menu") && (s:MenuBuildt == 0) 
        if (&filetype == "python") || (g:PTC_AllFiles == 1)
            amenu &Tools.&Start\ Calltips :call <SID>DoCalltips()<CR>
            amenu &Tools.&Stop\ Calltips :call <SID>EndCalltips()<CR>
            echo "python_caltips BuildMenu"
            let s:MenuBuildt = 1
        endif
    endif    
endfunc

func! <SID>TearDownMenu()
" Teardown menu when we leave filtype=python
    if has("menu") && (s:MenuBuildt == 1) 
        if (&filetype == "python") && (g:PTC_AllFiles == 0)
            aunmenu &Tools.&Start\ Calltips
            aunmenu &Tools.&Stop\ Calltips
            echo "python_caltips TearDownMenu"
            let s:MenuBuildt = 0
        endif
    endif        
endfunc

if has('python')
    function! <SID>DefPython()
        
python << PYTHONEOF
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
    # import pywin.debugger
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
        vim.command('silent! bwipeout Python_Calltips')
    except:
        pass

def CT_Init():
    """creat a new calltips windows"""

    global helpBuffer
    bname = vim.current.buffer.name
    vim.command('silent rightbelow new Python_Calltips')
    vim.command('set buftype=nofile')
    vim.command('set nonumber')
    vim.command('set nowrap')
    vim.command('resize 5')
    vim.command('set noswapfile')
    helpBuffer = vim.current.buffer
    while True:
        vim.command('wincmd w')   #switch back window
        if bname == vim.current.buffer.name:
            break
    vim.command('autocmd CursorHold *.py python CT_ImportObject()')
    vim.command('set updatetime=5000')
    from sys import path
    path.extend(['.','..'])  #add current path and parent path

def CT_Clear():
    """clear calltips buffer and unused python object"""

    ALL = ['CT_GetWordUnderCursor', 'CT_AutoComplete', 'CT_GetHelp',\
           'CT_ImportObject', 'CT_CallTips', 'CT_mapkeys', 'CT_unmapkeys',\
           'CT_Init', 'CT_Clear', '__builtin__', '__builtins__', '__doc__', \
           '__name__', 'vim', 'letters', 'helpBuffer', 'CT_STRINGTYPE', \
           'CT_LISTTYPE', 'CT_DICTTYPE', 'CT_FILETYPE', 'CT_SETTYPE', 'Set']
          
    #TODO: staale we should getride of the buffer or hide it? Or lett the user decide?
    #TODO: tocer - I'm afraid of unused python variable disturb user. So I delete it.
    #TODO: and does it cause other bug?
    helpBuffer[:] = None  #clear help buffer
    vim.command('autocmd! CursorHold *.py')
    
    for object in globals().keys():
        if object not in ALL:
            try:
                exec('del %s' % object) in globals()
            except: pass
                #print 'Fail: del %s' % object


CT_STRINGTYPE = str
CT_LISTTYPE   = list
CT_DICTTYPE   = dict
CT_FILETYPE   = file
CT_SETTYPE    = Set
PYTHONEOF

endfunction

call <SID>DefPython()
endif

" -------------------------------------------------------------------
"  Main part of aplication must (??) come after all function 
"  declarations. This is a bit strage as this is not a requirement
"  when we creta functions in .vimrcHow 
" -------------------------------------------------------------------
call <SID>SetEventHooks()
