from generation_support import *
invoke(lambda: generate(sys.argv[1],'articles') if len(sys.argv)==2 else 2)
