# count comment lines, empty lines

BEGIN {
    commentLineCount = emptyLineCount = othersCount = 0
}
/^[ \t]*#/ { 
    commentLineCount = commentLineCount + 1
    next
}
/^[ \t]*$/ {
    emptyLineCount = emptyLineCount + 1
    next
}
{
    othersCount = othersCount + 1
}
END {
    print "comment lines: ", commentLineCount
    print "empty lines: ", emptyLineCount
    print "other lines: ", othersCount
}
