set PI=c:\python26\python.exe

del addlinenum.output
%PI% .\tinyawk.py -f addlinenum.awk addlinenum.awk > addlinenum.output
if ERRORLEVEL 1 goto errorend

del countcomment.output
%PI% .\tinyawk.py -f countcomment.awk countcomment.awk > countcomment.output
if ERRORLEVEL 1 goto errorend

del printfibo.output
%PI% .\tinyawk.py -f printfibo.awk > printfibo.output
if ERRORLEVEL 1 goto errorend

del removedup.output
%PI% .\tinyawk.py -f removedup.awk removedup.awk > removedup.output
if ERRORLEVEL 1 goto errorend

del wc.output
%PI% .\tinyawk.py -f wc.awk wc.awk > wc.output
if ERRORLEVEL 1 goto errorend

goto normalend

:errorend
echo error occured

:normalend
