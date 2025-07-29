fork_test1 = '''
    add 0 #1
    je 0 #1 label_fk
    ret #2
label_fk:
    ret #7
'''

move_test1 = '''
add 0 #1
je 0 #1 label_down
je 0 #2 label_right
je 0 #3 label_up
je 0 #4 label_left
label_down:
ret #2
label_right:
ret #4
label_up:
ret #1
label_left:
ret #3
'''