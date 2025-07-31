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

move_test2 = '''
je 0 #0 $down
je 0 #1 $right
je 0 #2 $up
je 0 #3 $left

$down:
inc 0      
ret #2     

$right:
inc 0
ret #4   

$up:
inc 0
ret #1    

$left:
inc 0
mov 0 #0    
ret #3        
'''

chest_test = '''
    jg 50 #0 solve_chest
open_chest:
    ret #5
solve_chest:
    je 50 #1 solve_chal1
    ret #0
solve_chal1:
    // swap(51, 57)
    mov 72 51
    mov 51 57
    mov 57 72

    mov 72 52
    mov 52 56
    mov 56 72

    mov 72 53
    mov 53 55
    mov 55 72
    je 0 0 end
end:
    ret #5
    '''