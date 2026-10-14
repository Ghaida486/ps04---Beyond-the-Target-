from feed_support import *
invoke(lambda: collect(sys.argv[1],'feed') if len(sys.argv)==2 else 2)
