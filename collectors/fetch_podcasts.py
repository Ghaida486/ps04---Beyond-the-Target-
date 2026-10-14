from feed_support import *
invoke(lambda: collect(sys.argv[1],'podcast') if len(sys.argv)==2 else 2)
